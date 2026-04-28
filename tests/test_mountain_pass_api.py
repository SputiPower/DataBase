from copy import deepcopy

from sqlalchemy.orm import Session, sessionmaker

from app.db.enums import PassStatus
from app.db.models import MountainPass


def build_payload() -> dict:
    return {
        "beauty_title": "пер. ",
        "title": "Пхия",
        "other_titles": "Триев",
        "connect": "",
        "add_time": "2021-09-22 13:18:13",
        "user": {
            "email": "qwerty@mail.ru",
            "fam": "Пупкин",
            "name": "Василий",
            "otc": "Иванович",
            "phone": "+7 555 55 55",
        },
        "coords": {
            "latitude": "45.3842",
            "longitude": "7.1525",
            "height": 1200,
        },
        "level": {
            "winter": "",
            "summer": "1А",
            "autumn": "1А",
            "spring": "",
        },
        "images": [
            {"data": "aGVsbG8=", "title": "Седловина"},
            {"data": "d29ybGQ=", "title": "Подъём"},
        ],
    }


def create_mountain_pass(client) -> int:
    response = client.post("/submitData", json=build_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    assert body["message"] == "Отправлено успешно"
    assert body["id"] is not None
    return body["id"]


def test_post_submit_data_and_get_by_id(client) -> None:
    record_id = create_mountain_pass(client)

    response = client.get(f"/submitData/{record_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Пхия"
    assert body["status"] == "new"
    assert body["user"]["email"] == "qwerty@mail.ru"
    assert body["coords"]["height"] == 1200
    assert len(body["images"]) == 2


def test_patch_updates_record_with_new_status(client) -> None:
    record_id = create_mountain_pass(client)
    payload = build_payload()
    payload["title"] = "Пхия обновлённая"
    payload["coords"]["height"] = 1450
    payload["level"]["winter"] = "2А"
    payload["images"] = [{"data": "bmV3LWltYWdl", "title": "Новый кадр"}]

    patch_response = client.patch(f"/submitData/{record_id}", json=payload)

    assert patch_response.status_code == 200
    assert patch_response.json() == {"state": 1, "message": None}

    get_response = client.get(f"/submitData/{record_id}")
    body = get_response.json()
    assert body["title"] == "Пхия обновлённая"
    assert body["coords"]["height"] == 1450
    assert body["level"]["winter"] == "2А"
    assert len(body["images"]) == 1
    assert body["user"]["email"] == "qwerty@mail.ru"


def test_patch_rejected_for_non_new_status(client, session_factory: sessionmaker[Session]) -> None:
    record_id = create_mountain_pass(client)

    with session_factory() as session:
        mountain_pass = session.get(MountainPass, record_id)
        assert mountain_pass is not None
        mountain_pass.status = PassStatus.PENDING
        session.commit()

    payload = build_payload()
    payload["title"] = "Изменение после модерации"
    response = client.patch(f"/submitData/{record_id}", json=payload)

    assert response.status_code == 409
    assert response.json() == {
        "state": 0,
        "message": "Редактирование запрещено, так как статус записи не new",
    }


def test_patch_rejected_if_user_data_changed(client) -> None:
    record_id = create_mountain_pass(client)
    payload = build_payload()
    payload["user"]["phone"] = "+7 999 99 99"

    response = client.patch(f"/submitData/{record_id}", json=payload)

    assert response.status_code == 400
    assert response.json() == {
        "state": 0,
        "message": "Редактирование данных пользователя запрещено",
    }


def test_get_perevals_by_user_email_returns_user_records(client) -> None:
    first_payload = build_payload()
    second_payload = deepcopy(build_payload())
    second_payload["title"] = "Архызский"
    second_payload["other_titles"] = "Второй"

    first_response = client.post("/submitData", json=first_payload)
    second_response = client.post("/submitData", json=second_payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    response = client.get("/submitData", params={"user__email": "qwerty@mail.ru"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {item["title"] for item in body} == {"Пхия", "Архызский"}
    assert all(item["status"] == "new" for item in body)
