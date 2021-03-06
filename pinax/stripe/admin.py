from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import (  # @@@ make all these read-only
    Account,
    BankAccount,
    BitcoinReceiver,
    Card,
    Charge,
    Coupon,
    Customer,
    Event,
    EventProcessingException,
    Invoice,
    InvoiceItem,
    Plan,
    Subscription,
    Transfer,
    TransferChargeFee,
    UserAccount
)


def user_search_fields():
    User = get_user_model()
    fields = [
        "user__{0}".format(User.USERNAME_FIELD)
    ]
    if "email" in [f.name for f in User._meta.fields]:  # pragma: no branch
        fields += ["user__email"]
    return fields


def customer_search_fields():
    return [
        "customer__{0}".format(field)
        for field in user_search_fields()
    ]


class CustomerHasCardListFilter(admin.SimpleListFilter):
    title = "card presence"
    parameter_name = "has_card"

    def lookups(self, request, model_admin):
        return [
            ["yes", "Has Card"],
            ["no", "Does Not Have a Card"]
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(card__isnull=True)
        elif self.value() == "no":
            return queryset.filter(card__isnull=False)
        return queryset.all()


class InvoiceCustomerHasCardListFilter(admin.SimpleListFilter):
    title = "card presence"
    parameter_name = "has_card"

    def lookups(self, request, model_admin):
        return [
            ["yes", "Has Card"],
            ["no", "Does Not Have a Card"]
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(customer__card__isnull=True)
        elif self.value() == "no":
            return queryset.filter(customer__card__isnull=False)
        return queryset.all()


class CustomerSubscriptionStatusListFilter(admin.SimpleListFilter):
    title = "subscription status"
    parameter_name = "sub_status"

    def lookups(self, request, model_admin):
        statuses = [
            [x, x.replace("_", " ").title()]
            for x in Subscription.objects.all().values_list(
                "status",
                flat=True
            ).distinct()
        ]
        statuses.append(["none", "No Subscription"])
        return statuses

    def queryset(self, request, queryset):
        if self.value() == "none":
            # Get customers with 0 subscriptions
            return queryset.annotate(subs=Count("subscription")).filter(subs=0)
        elif self.value():
            # Get customer pks without a subscription with this status
            customers = Subscription.objects.filter(
                status=self.value()).values_list(
                "customer", flat=True).distinct()
            # Filter by those customers
            return queryset.filter(pk__in=customers)
        return queryset.all()


class AccountListFilter(admin.SimpleListFilter):
    title = "account"
    parameter_name = "stripe_account"

    def lookups(self, request, model_admin):
        return [("none", "Without Account")] + [(a.pk, str(a)) for a in Account.objects.all()]

    def queryset(self, request, queryset):
        if self.value() == "none":
            return queryset.filter(stripe_account__isnull=True)
        if self.value():
            return queryset.filter(stripe_account__pk=self.value())
        return queryset


admin.site.register(
    Charge,
    list_display=[
        "stripe_id",
        "customer",
        "amount",
        "description",
        "paid",
        "disputed",
        "refunded",
        "receipt_sent",
        "created_at",
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
        "invoice__stripe_id",
    ] + customer_search_fields(),
    list_filter=[
        "paid",
        "disputed",
        "refunded",
        "created_at",
    ],
    raw_id_fields=[
        "customer",
        "invoice",
    ],
)

admin.site.register(
    EventProcessingException,
    list_display=[
        "message",
        "event",
        "created_at"
    ],
    search_fields=[
        "message",
        "traceback",
        "data"
    ],
    raw_id_fields=[
        "event"
    ],
)

admin.site.register(
    Event,
    raw_id_fields=["customer", "stripe_account"],
    list_display=[
        "stripe_id",
        "kind",
        "livemode",
        "valid",
        "processed",
        "created_at",
        "stripe_account",
    ],
    list_filter=[
        "kind",
        "created_at",
        "valid",
        "processed",
        AccountListFilter,
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
        "validated_message",
        "=stripe_account__stripe_id",
    ] + customer_search_fields(),
)


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    max_num = 0


class CardInline(admin.TabularInline):
    model = Card
    extra = 0
    max_num = 0


class BitcoinReceiverInline(admin.TabularInline):
    model = BitcoinReceiver
    extra = 0
    max_num = 0


def subscription_status(obj):
    return ", ".join([subscription.status for subscription in obj.subscription_set.all()])
subscription_status.short_description = "Subscription Status"  # noqa


admin.site.register(
    Customer,
    raw_id_fields=["user", "stripe_account"],
    list_display=[
        "stripe_id",
        "user",
        "account_balance",
        "currency",
        "delinquent",
        "default_source",
        subscription_status,
        "date_purged",
        "stripe_account",
    ],
    list_filter=[
        "delinquent",
        CustomerHasCardListFilter,
        CustomerSubscriptionStatusListFilter,
        AccountListFilter,
    ],
    search_fields=[
        "stripe_id",
        "=stripe_account__stripe_id"
    ] + user_search_fields(),
    inlines=[
        SubscriptionInline,
        CardInline,
        BitcoinReceiverInline
    ]
)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    max_num = 0


def customer_has_card(obj):
    return obj.customer.card_set.exclude(fingerprint="").exists()
customer_has_card.short_description = "Customer Has Card"  # noqa


def customer_user(obj):
    User = get_user_model()
    username = getattr(obj.customer.user, User.USERNAME_FIELD)
    email = getattr(obj, "email", "")
    return "{0} <{1}>".format(
        username,
        email
    )
customer_user.short_description = "Customer"  # noqa


admin.site.register(
    Invoice,
    raw_id_fields=["customer"],
    list_display=[
        "stripe_id",
        "paid",
        "closed",
        customer_user,
        customer_has_card,
        "period_start",
        "period_end",
        "subtotal",
        "total",
    ],
    search_fields=[
        "stripe_id",
        "customer__stripe_id",
    ] + customer_search_fields(),
    list_filter=[
        InvoiceCustomerHasCardListFilter,
        "paid",
        "closed",
        "attempted",
        "attempt_count",
        "created_at",
        "date",
        "period_end",
        "total",
    ],
    inlines=[
        InvoiceItemInline
    ],
)

admin.site.register(
    Plan,
    raw_id_fields=["stripe_account"],
    list_display=[
        "stripe_id",
        "name",
        "amount",
        "currency",
        "interval",
        "interval_count",
        "trial_period_days",
        "stripe_account",
    ],
    search_fields=[
        "stripe_id",
        "name",
        "=stripe_account__stripe_id",
    ] + customer_search_fields(),
    list_filter=[
        "currency",
        AccountListFilter,
    ],
    readonly_fields=[
        "stripe_id",
        "name",
        "amount",
        "currency",
        "interval",
        "interval_count",
        "trial_period_days",
        "statement_descriptor",
        "created_at",
    ],
)


admin.site.register(
    Coupon,
    list_display=[
        "stripe_id",
        "amount_off",
        "currency",
        "percent_off",
        "duration",
        "duration_in_months",
        "redeem_by",
        "valid"
    ],
    search_fields=[
        "stripe_id",
    ],
    list_filter=[
        "currency",
        "valid",
    ],
    readonly_fields=[
        "stripe_id",
        "amount_off",
        "currency",
        "duration",
        "duration_in_months",
        "max_redemptions",
        "metadata",
        "percent_off",
        "redeem_by",
        "times_redeemed",
        "valid",
        "created_at"
    ],
)


class TransferChargeFeeInline(admin.TabularInline):
    model = TransferChargeFee
    extra = 0
    max_num = 0


admin.site.register(
    Transfer,
    raw_id_fields=["event", "stripe_account"],
    list_display=[
        "stripe_id",
        "amount",
        "status",
        "date",
        "description",
        "stripe_account",
    ],
    search_fields=[
        "stripe_id",
        "event__stripe_id",
        "=stripe_account__stripe_id",
    ],
    inlines=[
        TransferChargeFeeInline
    ],
    list_filter=[
        AccountListFilter,
    ],
)


admin.site.register(
    Account,
    raw_id_fields=["user"],
    list_display=[
        "stripe_id",
        "type",
        "country",
        "transfers_enabled",
        "charges_enabled"
    ],
    search_fields=[
        "stripe_id",
    ]
)

admin.site.register(
    BankAccount,
    raw_id_fields=["account"],
    list_display=[
        "stripe_id",
        "account",
        "account_holder_type",
        "account_holder_name",
        "currency",
        "default_for_currency",
        "bank_name",
        "country",
        "last4"
    ],
    search_fields=[
        "stripe_id",
    ]
)

admin.site.register(
    UserAccount,
    raw_id_fields=["user", "customer"],
    list_display=["user", "customer"],
    search_fields=[
        "=customer__stripe_id",
        "=user__email",
    ]
)
