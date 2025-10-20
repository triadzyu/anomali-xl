import time
from random import randint

import requests

from app.client.balance import settlement_balance
from app.client.encrypt import BASE_CRYPTO_URL
from app.client.engsel import get_family, get_package_details
from app.menus.util import pause
from app.service.auth import AuthInstance
from app.type_dict import PaymentItem


# Purchase
def purchase_by_family(
        family_code: str,
        use_decoy: bool,
        pause_on_success: bool = True,
        token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    if use_decoy:
        # Balance; Decoy XCP
        url = BASE_CRYPTO_URL + "/decoyxcp"

        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Gagal mengambil data decoy package.")
            pause()
            return None

        decoy_data = response.json()
        decoy_package_detail = get_package_details(
            api_key,
            tokens,
            decoy_data["family_code"],
            decoy_data["variant_code"],
            decoy_data["order"],
            decoy_data["is_enterprise"],
            decoy_data["migration_type"],
        )

        balance_treshold = decoy_package_detail["package_option"]["price"]
        print(f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!")
        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
        if balance_answer.lower() != "y":
            print("Pembelian dibatalkan oleh user.")
            pause()
            return None

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print(f"Failed to get family data for code: {family_code}.")
        pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]

    print("-------------------------------------------------------")
    successful_purchases = []
    packages_count = 0
    for variant in variants:
        packages_count += len(variant["package_options"])

    purchase_count = 0
    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()

            option_name = option["name"]
            option_order = option["order"]
            option_price = option["price"]

            purchase_count += 1
            print(f"Pruchase {purchase_count} of {packages_count}...")
            print(f"Trying to buy: {variant_name} - {option_order}. {option_name} - {option['price']}")

            payment_items = []

            try:
                if use_decoy:
                    decoy_package_detail = get_package_details(
                        api_key,
                        tokens,
                        decoy_data["family_code"],
                        decoy_data["variant_code"],
                        decoy_data["order"],
                        decoy_data["is_enterprise"],
                        decoy_data["migration_type"],
                    )

                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                print(f"Exception occurred while fetching package details: {e}")
                print(f"Failed to get package details for {variant_name} - {option_name}. Skipping.")
                continue

            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + target_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )

            if use_decoy:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=str(randint(1000, 9999)) + decoy_package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )

            res = None

            overwrite_amount = target_package_detail["package_option"]["price"]
            if use_decoy:
                overwrite_amount += decoy_package_detail["package_option"]["price"]

            try:
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "BUY_PACKAGE",
                    False,
                    overwrite_amount,
                )

                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "Unknown error")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())

                        print(f"Adjusted total amount to: {valid_amount}")
                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "BUY_PACKAGE",
                            False,
                            valid_amount,
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            successful_purchases.append(
                                f"{variant_name}|{option_order}. {option_name} - {option_price}"
                            )

                            if pause_on_success:
                                print("Purchase successful!")
                                pause()
                            else:
                                print("Purchase successful!")
                else:
                    successful_purchases.append(
                        f"{variant_name}|{option_order}. {option_name} - {option_price}"
                    )
                    if pause_on_success:
                        print("Purchase successful!")
                        pause()
                    else:
                        print("Purchase successful!")

            except Exception as e:
                print(f"Exception occurred while creating order: {e}")
                res = None
            print("-------------------------------------------------------")

    print(f"Total successful purchases for family {family_name}: {len(successful_purchases)}")
    if len(successful_purchases) > 0:
        print("-------------------------------------------------------")
        print("Successful purchases:")
        for purchase in successful_purchases:
            print(f"- {purchase}")
    print("-------------------------------------------------------")
    pause()


def purchase_n_times(
        n: int,
        family_code: str,
        variant_code: str,
        option_order: int,
        use_decoy: bool,
        delay_seconds: int = 0,
        pause_on_success: bool = False,
        token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    if use_decoy:
        # Balance; Decoy XCP
        url = BASE_CRYPTO_URL + "/decoyxcp"

        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Gagal mengambil data decoy package.")
            pause()
            return None

        decoy_data = response.json()
        decoy_package_detail = get_package_details(
            api_key,
            tokens,
            decoy_data["family_code"],
            decoy_data["variant_code"],
            decoy_data["order"],
            decoy_data["is_enterprise"],
            decoy_data["migration_type"],
        )

        balance_treshold = decoy_package_detail["package_option"]["price"]
        print(f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!")
        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
        if balance_answer.lower() != "y":
            print("Pembelian dibatalkan oleh user.")
            pause()
            return None

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print(f"Failed to get family data for code: {family_code}.")
        pause()
        return None
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = None
    for variant in variants:
        if variant["package_variant_code"] == variant_code:
            target_variant = variant
            break
    if not target_variant:
        print(f"Variant code {variant_code} not found in family {family_name}.")
        pause()
        return None
    target_option = None
    for option in target_variant["package_options"]:
        if option["order"] == option_order:
            target_option = option
            break
    if not target_option:
        print(f"Option order {option_order} not found in variant {target_variant['name']}.")
        pause()
        return None
    option_name = target_option["name"]
    option_price = target_option["price"]
    print("-------------------------------------------------------")
    successful_purchases = []

    for i in range(n):
        print(f"Pruchase {i + 1} of {n}...")
        print(f"Trying to buy: {target_variant['name']} - {option_order}. {option_name} - {option_price}")

        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}

        payment_items = []

        try:
            if use_decoy:
                decoy_package_detail = get_package_details(
                    api_key,
                    tokens,
                    decoy_data["family_code"],
                    decoy_data["variant_code"],
                    decoy_data["order"],
                    decoy_data["is_enterprise"],
                    decoy_data["migration_type"],
                )

            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None,
                None,
            )
        except Exception as e:
            print(f"Exception occurred while fetching package details: {e}")
            print(f"Failed to get package details for {target_variant['name']} - {option_name}. Skipping.")
            continue

        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )

        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

        res = None

        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "BUY_PACKAGE",
                False,
                overwrite_amount,
            )

            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())

                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "BUY_PACKAGE",
                        False,
                        valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(
                            f"{target_variant['name']}|{option_order}. {option_name} - {option_price}"
                        )

                        if pause_on_success:
                            print("Purchase successful!")
                            pause()
                        else:
                            print("Purchase successful!")
            else:
                successful_purchases.append(
                    f"{target_variant['name']}|{option_order}. {option_name} - {option_price}"
                )
                if pause_on_success:
                    print("Purchase successful!")
                    pause()
                else:
                    print("Purchase successful!")
        except Exception as e:
            print(f"Exception occurred while creating order: {e}")
            res = None
        print("-------------------------------------------------------")

        if delay_seconds > 0 and i < n - 1:
            print(f"Waiting for {delay_seconds} seconds before next purchase...")
            time.sleep(delay_seconds)

    print(
        f"Total successful purchases {len(successful_purchases)}/{n} for:\nFamily: {family_name}\nVariant: {target_variant['name']}\nOption: {option_order}. {option_name} - {option_price}")
    if len(successful_purchases) > 0:
        print("-------------------------------------------------------")
        print("Successful purchases:")
        for idx, purchase in enumerate(successful_purchases):
            print(f"{idx + 1}. {purchase}")
    print("-------------------------------------------------------")
    pause()
    return True


def purchase_loop(
        loop: int,
        family_code: str,
        order: int,
        use_decoy: bool,
        delay: int = 0,
        pause_on_success: bool = False,
):
    family_name = None
    target_variant = None
    successful_purchases = []

    for i in range(loop):
        print(f"Pruchase {i + 1} of {loop}...")

        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}

        # Find the package variant and option from family data
        family_data = get_family(api_key, tokens, family_code)
        if not family_data:
            print(f"Failed to get family data for code: {family_code}.")
            pause()
            return

        family_name = family_data["package_family"]["name"]

        target_variant = None
        target_option = None
        for variant in family_data["package_variants"]:
            for option in variant["package_options"]:
                if option["order"] == order:
                    target_variant = variant
                    target_option = option
                    break
            if target_option:
                break

        if not target_variant or not target_option:
            print(f"Package with order {order} not found in family {family_code}.")
            pause()
            return

        option_name = target_option["name"]
        option_price = target_option["price"]

        variant_code = target_variant["package_variant_code"]

        if use_decoy:
            # Balance; Decoy XCP
            url = "https://me.mashu.lol/pg-decoy-xcp.json"

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print("Gagal mengambil data decoy package.")
                pause()
                return None

            decoy_data = response.json()
            decoy_package_detail = get_package_details(
                api_key,
                tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"],
            )

            balance_treshold = decoy_package_detail["package_option"]["price"]
            print(f"Pastikan sisa balance KURANG DARI Rp{balance_treshold}!!!")

        tokens = AuthInstance.get_active_tokens()

        try:
            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                variant_code,
                order,
                None,
                None,
            )
        except Exception as e:
            print(f"Exception occurred while fetching package details: {e}")
            print(f"Failed to get package details. Aborting.")
            return

        payment_items = []
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(order) + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )

        if use_decoy:
            decoy_package_detail = get_package_details(
                api_key,
                tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"],
            )
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(decoy_data["order"]) + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "BUY_PACKAGE",
                False,
                overwrite_amount,
            )

            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                print(f"Purchase failed: {error_msg}")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())

                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "BUY_PACKAGE",
                        False,
                        valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(
                            f"{target_variant['name']}|{option_name} - {option_price}"
                        )
                        print(f"Purchase successful! {i + 1}")
                        if pause_on_success:
                            choice = input("Lanjut Dor? (Y/N): ")
                            if choice.lower() == 'n':
                                return False
            else:
                successful_purchases.append(
                    f"{target_variant['name']}|{option_name} - {option_price}"
                )
                print(f"Purchase successful! {i + 1}")
                if pause_on_success:
                    choice = input("Lanjut Dor? (Y/N): ")
                    if choice.lower() == 'n':
                        return False

        except Exception as e:
            print(f'Exception occurred while creating order: {e}')
            return False

        print("-------------------------------------------------------")
        if delay > 0 and i < loop - 1:
            print(f"Waiting for {delay} seconds before next purchase...")
            time.sleep(delay)

    print(
        f"Total successful purchases {len(successful_purchases)}/{loop} for:\nFamily: {family_name}\nVariant: {target_variant['name']}")
    if len(successful_purchases) > 0:
        print("-------------------------------------------------------")
        print("Successful purchases:")
        for idx, purchase in enumerate(successful_purchases):
            print(f"{idx + 1}. {purchase}")
    print("-------------------------------------------------------")
    pause()
    return True
