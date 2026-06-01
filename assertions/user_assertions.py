from pytest_check import check
import allure
from models.test_user_model import (
    PatchUserPayload,
    PatchUserResponse,
    UserTestData,
)


@allure.step("Проверка результата частичного обновления пользователя")
def assert_partial_user_update(
    response: PatchUserResponse,
    original_user: UserTestData,
    patch_payload: PatchUserPayload,
) -> None:

    patch_data = patch_payload.model_dump(exclude_none=True)

    changed_fields = set(patch_data.keys())

    for field_name, expected_value in patch_data.items():
        actual_value = getattr(response, field_name)

        check.equal(
            actual_value,
            expected_value,
            (
                f"Поле '{field_name}' не обновилось. "
                f"ОР: {expected_value} "
                f"ФР: {actual_value}"
            ),
        )

    original_user_data = original_user.model_dump()

    unchanged_fields = (
        set(original_user_data) - changed_fields - {"password", "passwordRepeat"}
    )

    for field_name in unchanged_fields:
        actual_value = getattr(response, field_name)
        expected_value = getattr(original_user, field_name)

        check.equal(
            actual_value,
            expected_value,
            (
                f"Поле '{field_name}' изменилось после PATCH. "
                f"ОР: {expected_value}, ФР: {actual_value}"
            ),
        )
