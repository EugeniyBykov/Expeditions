"""
Integration tests for the expedition management core logic.

Uses an in-memory SQLite database via aiosqlite.
The `datetime` module is patched in the service layer where needed
so that naive timestamps from SQLite compare correctly.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.models.base import UserRole, ExpeditionStatus, ExpeditionMemberState
from app.models.expedition import Expedition
from app.models.expedition_member import ExpeditionMember
from app.models.user import User
from tests.conftest import auth_headers

# A naive datetime in the past used as a consistent "now" baseline across tests
PAST = datetime(2020, 1, 1, 0, 0, 0)
# A naive datetime further in the past used as expedition start_at
EARLIER = datetime(2019, 6, 1, 0, 0, 0)
# A naive datetime in the far future
FUTURE = datetime(2099, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def chief(db_session):
    user = User(email="chief@test.com", name="Chief", role=UserRole.CHIEF)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def member(db_session):
    user = User(email="member@test.com", name="Member", role=UserRole.MEMBER)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def draft_expedition(db_session, chief):
    exp = Expedition(
        title="Test Expedition",
        status=ExpeditionStatus.DRAFT,
        start_at=EARLIER,
        capacity=10,
        chief_id=chief.id,
    )
    db_session.add(exp)
    await db_session.commit()
    await db_session.refresh(exp)
    return exp


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_unauthenticated_request_returns_401(client):
    response = await client.post("/expeditions", json={})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Create expedition
# ---------------------------------------------------------------------------


async def test_chief_can_create_expedition(client, chief):
    payload = {
        "title": "Arctic Journey",
        "start_at": "2030-01-01T00:00:00Z",
        "capacity": 5,
    }
    response = await client.post(
        "/expeditions", json=payload, headers=auth_headers(chief)
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Arctic Journey"
    assert data["status"] == "draft"
    assert data["chief_id"] == str(chief.id)


async def test_member_cannot_create_expedition(client, member):
    payload = {
        "title": "Arctic Journey",
        "start_at": "2030-01-01T00:00:00Z",
        "capacity": 5,
    }
    response = await client.post(
        "/expeditions", json=payload, headers=auth_headers(member)
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# draft -> ready
# ---------------------------------------------------------------------------


async def test_mark_ready_transitions_status(client, chief, draft_expedition):
    response = await client.post(
        f"/expeditions/{draft_expedition.id}/ready",
        headers=auth_headers(chief),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_mark_ready_requires_chief(client, member, draft_expedition):
    response = await client.post(
        f"/expeditions/{draft_expedition.id}/ready",
        headers=auth_headers(member),
    )
    assert response.status_code == 403


async def test_mark_ready_requires_draft_status(
    client, chief, db_session, draft_expedition
):
    draft_expedition.status = ExpeditionStatus.ACTIVE
    db_session.add(draft_expedition)
    await db_session.commit()

    response = await client.post(
        f"/expeditions/{draft_expedition.id}/ready",
        headers=auth_headers(chief),
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# ready -> active
# ---------------------------------------------------------------------------


async def test_mark_active_fails_before_start_time(
    client, chief, db_session, draft_expedition
):
    draft_expedition.status = ExpeditionStatus.READY
    draft_expedition.start_at = FUTURE
    db_session.add(draft_expedition)
    await db_session.commit()

    with patch("app.services.expedition.datetime") as mock_dt:
        mock_dt.now.return_value = PAST  # PAST < FUTURE -> should be blocked
        response = await client.post(
            f"/expeditions/{draft_expedition.id}/active",
            headers=auth_headers(chief),
        )
    assert response.status_code == 400
    assert "start_at" in response.json()["detail"]


async def test_mark_active_fails_with_fewer_than_two_confirmed_members(
    client, chief, member, db_session, draft_expedition
):
    draft_expedition.status = ExpeditionStatus.READY
    db_session.add(draft_expedition)
    db_session.add(
        ExpeditionMember(
            expedition_id=draft_expedition.id,
            user_id=member.id,
            state=ExpeditionMemberState.CONFIRMED,
            invited_at=EARLIER,
            confirmed_at=EARLIER,
        )
    )
    await db_session.commit()

    with patch("app.services.expedition.datetime") as mock_dt:
        mock_dt.now.return_value = PAST  # PAST > EARLIER (start_at) -> time OK
        response = await client.post(
            f"/expeditions/{draft_expedition.id}/active",
            headers=auth_headers(chief),
        )
    assert response.status_code == 400
    assert "2" in response.json()["detail"]


async def test_mark_active_fails_when_member_in_another_active_expedition(
    client, chief, db_session, draft_expedition
):
    other_chief = User(email="other_chief@test.com", name="OC", role=UserRole.CHIEF)
    busy_member = User(email="busy@test.com", name="Busy", role=UserRole.MEMBER)
    free_member = User(email="free@test.com", name="Free", role=UserRole.MEMBER)
    db_session.add_all([other_chief, busy_member, free_member])
    await db_session.flush()

    other_exp = Expedition(
        title="Other Expedition",
        status=ExpeditionStatus.ACTIVE,
        start_at=EARLIER,
        capacity=10,
        chief_id=other_chief.id,
    )
    db_session.add(other_exp)
    await db_session.flush()

    # busy_member is confirmed in the active other_exp
    db_session.add(
        ExpeditionMember(
            expedition_id=other_exp.id,
            user_id=busy_member.id,
            state=ExpeditionMemberState.CONFIRMED,
            invited_at=EARLIER,
            confirmed_at=EARLIER,
        )
    )

    # Our expedition: READY with busy_member + free_member confirmed
    draft_expedition.status = ExpeditionStatus.READY
    db_session.add(draft_expedition)
    for m in [busy_member, free_member]:
        db_session.add(
            ExpeditionMember(
                expedition_id=draft_expedition.id,
                user_id=m.id,
                state=ExpeditionMemberState.CONFIRMED,
                invited_at=EARLIER,
                confirmed_at=EARLIER,
            )
        )
    await db_session.commit()

    with patch("app.services.expedition.datetime") as mock_dt:
        mock_dt.now.return_value = PAST
        response = await client.post(
            f"/expeditions/{draft_expedition.id}/active",
            headers=auth_headers(chief),
        )
    assert response.status_code == 400
    assert "another active expedition" in response.json()["detail"]


async def test_mark_active_success(client, chief, db_session, draft_expedition):
    member1 = User(email="m1@test.com", name="M1", role=UserRole.MEMBER)
    member2 = User(email="m2@test.com", name="M2", role=UserRole.MEMBER)
    db_session.add_all([member1, member2])
    await db_session.flush()

    draft_expedition.status = ExpeditionStatus.READY
    db_session.add(draft_expedition)
    for m in [member1, member2]:
        db_session.add(
            ExpeditionMember(
                expedition_id=draft_expedition.id,
                user_id=m.id,
                state=ExpeditionMemberState.CONFIRMED,
                invited_at=EARLIER,
                confirmed_at=EARLIER,
            )
        )
    await db_session.commit()

    with patch("app.services.expedition.datetime") as mock_dt:
        mock_dt.now.return_value = PAST  # PAST > EARLIER (start_at)
        response = await client.post(
            f"/expeditions/{draft_expedition.id}/active",
            headers=auth_headers(chief),
        )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


# ---------------------------------------------------------------------------
# active -> finished
# ---------------------------------------------------------------------------


async def test_mark_finished_transitions_status(
    client, chief, db_session, draft_expedition
):
    draft_expedition.status = ExpeditionStatus.ACTIVE
    db_session.add(draft_expedition)
    await db_session.commit()

    response = await client.post(
        f"/expeditions/{draft_expedition.id}/finished",
        headers=auth_headers(chief),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "finished"


async def test_mark_finished_requires_active_status(client, chief, draft_expedition):
    # expedition is in DRAFT status
    response = await client.post(
        f"/expeditions/{draft_expedition.id}/finished",
        headers=auth_headers(chief),
    )
    assert response.status_code == 400


async def test_finished_expedition_cannot_be_moved_to_ready(
    client, chief, db_session, draft_expedition
):
    draft_expedition.status = ExpeditionStatus.FINISHED
    db_session.add(draft_expedition)
    await db_session.commit()

    response = await client.post(
        f"/expeditions/{draft_expedition.id}/ready",
        headers=auth_headers(chief),
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Invite member
# ---------------------------------------------------------------------------


async def test_chief_can_invite_member(client, chief, member, draft_expedition):
    payload = {"expedition_id": str(draft_expedition.id), "user_id": str(member.id)}
    response = await client.post(
        "/expeditions/invite", json=payload, headers=auth_headers(chief)
    )
    assert response.status_code == 201
    data = response.json()
    assert data["state"] == "invited"
    assert data["user_id"] == str(member.id)


async def test_invite_fails_for_non_chief(client, member, draft_expedition):
    payload = {"expedition_id": str(draft_expedition.id), "user_id": str(member.id)}
    response = await client.post(
        "/expeditions/invite", json=payload, headers=auth_headers(member)
    )
    assert response.status_code == 403


async def test_invite_fails_for_chief_role_user(
    client, chief, db_session, draft_expedition
):
    another_chief = User(email="ac@test.com", name="AC", role=UserRole.CHIEF)
    db_session.add(another_chief)
    await db_session.commit()
    await db_session.refresh(another_chief)

    payload = {
        "expedition_id": str(draft_expedition.id),
        "user_id": str(another_chief.id),
    }
    response = await client.post(
        "/expeditions/invite", json=payload, headers=auth_headers(chief)
    )
    assert response.status_code == 400
    assert "member role" in response.json()["detail"]


async def test_invite_fails_when_expedition_not_draft(
    client, chief, member, db_session, draft_expedition
):
    draft_expedition.status = ExpeditionStatus.READY
    db_session.add(draft_expedition)
    await db_session.commit()

    payload = {"expedition_id": str(draft_expedition.id), "user_id": str(member.id)}
    response = await client.post(
        "/expeditions/invite", json=payload, headers=auth_headers(chief)
    )
    assert response.status_code == 400


async def test_duplicate_invite_fails(client, chief, member, draft_expedition):
    payload = {"expedition_id": str(draft_expedition.id), "user_id": str(member.id)}
    await client.post("/expeditions/invite", json=payload, headers=auth_headers(chief))
    response = await client.post(
        "/expeditions/invite", json=payload, headers=auth_headers(chief)
    )
    assert response.status_code == 400
    assert "already invited" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Confirm invitation
# ---------------------------------------------------------------------------


async def test_member_can_confirm_invitation(
    client, member, db_session, draft_expedition
):
    db_session.add(
        ExpeditionMember(
            expedition_id=draft_expedition.id,
            user_id=member.id,
            state=ExpeditionMemberState.INVITED,
            invited_at=EARLIER,
            confirmed_at=None,
        )
    )
    await db_session.commit()

    with patch("app.services.expedition.datetime") as mock_dt:
        mock_dt.now.return_value = PAST
        response = await client.post(
            f"/expeditions/invite/confirm/{draft_expedition.id}",
            headers=auth_headers(member),
        )
    assert response.status_code == 200
    assert response.json()["state"] == "confirmed"


async def test_confirm_already_confirmed_fails(
    client, member, db_session, draft_expedition
):
    db_session.add(
        ExpeditionMember(
            expedition_id=draft_expedition.id,
            user_id=member.id,
            state=ExpeditionMemberState.CONFIRMED,
            invited_at=EARLIER,
            confirmed_at=EARLIER,
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/expeditions/invite/confirm/{draft_expedition.id}",
        headers=auth_headers(member),
    )
    assert response.status_code == 400
    assert "already been confirmed" in response.json()["detail"]


async def test_uninvited_user_cannot_confirm(client, chief, draft_expedition):
    # chief is not invited as a member; should get 404
    response = await client.post(
        f"/expeditions/invite/confirm/{draft_expedition.id}",
        headers=auth_headers(chief),
    )
    assert response.status_code == 404
