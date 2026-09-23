"""A deterministic retail bank, delivered as eighteen monthly extracts.

The generator is the lab's ground truth. Every figure a technique's
``correct.sql`` must return is computed here, in Python, from the generator's own
records -- never by running SQL. A query that is wrong cannot then agree with
itself and pass.

The cases each technique needs are planted on purpose and listed in
``manifest.json``, so a technique never depends on the random draw happening to
contain one.

Extract contract, per batch directory ``batch=YYYY-MM/``:

- ``customers.csv``: one row per customer per batch at most. The first row for a
  customer is its first version; a later row is a change, dated by
  ``effective_date``. An effective date is never earlier than the customer's
  current version started (the one backdated correction respects this too).
- ``accounts.csv`` and ``account_holders.csv``: an account arrives exactly once,
  with its holders.
- ``transactions.csv``: rows arrive in the batch of their posting month, except
  those planted late, which arrive one or two batches after.
- ``fx_rates.csv``: every calendar day of the batch month.
- ``loan_events.csv``, ``promotions.csv``: the events of the batch month.
- ``branches.csv``, ``products.csv``: the full reference list, every batch.
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

START = date(2025, 1, 1)
END = date(2026, 6, 30)

CENT = Decimal("0.01")
SEGMENTS = ("mass", "affluent", "private")
CHANNELS = ("branch", "atm", "online", "mobile", "pos", "system")

BRANCHES = [
    ("B01", "Midtown", "New York", "East"),
    ("B02", "Back Bay", "Boston", "East"),
    ("B03", "Loop", "Chicago", "Central"),
    ("B04", "Uptown", "Dallas", "Central"),
    ("B05", "Mission", "San Francisco", "West"),
    ("B06", "Pioneer Square", "Seattle", "West"),
]
PRODUCTS = [
    ("CHK", "Everyday Checking", "deposit"),
    ("SAV", "Savings", "deposit"),
    ("CARD", "Credit Card", "credit"),
    ("LOAN", "Personal Loan", "lending"),
]
PROMOTED_PRODUCTS = ("CHK", "SAV", "CARD")

# Planted counts are fixed, not scaled, so the smallest test seed still has them.
N_CORRECTIONS = 4
N_INFERRED = 5
N_LATE_ACROSS_CHANGE = 6
CORRECTION_EFFECTIVE = date(2025, 9, 1)
CORRECTION_BATCH = "2026-03"
AS_REPORTED_BATCH = "2025-12"


def batch_of(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def month_starts() -> list[date]:
    out, d = [], START
    while d <= END:
        out.append(d)
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return out


BATCHES = [batch_of(m) for m in month_starts()]


def month_end(d: date) -> date:
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def add_batches(batch: str, n: int) -> str:
    i = min(BATCHES.index(batch) + n, len(BATCHES) - 1)
    return BATCHES[i]


def money(x: float | Decimal) -> Decimal:
    return Decimal(str(x)).quantize(CENT, rounding=ROUND_HALF_UP)


def days(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


@dataclass
class Customer:
    customer_id: str
    home_branch_id: str
    since: date
    # (effective_date, segment, arrival_batch), in effective order
    history: list[tuple[date, str, str]] = field(default_factory=list)

    def segment_at(self, d: date, known_by: str | None = None) -> str:
        seg = "Unknown"
        for eff, s, arrived in self.history:
            if known_by is not None and arrived > known_by:
                continue
            if eff <= d:
                seg = s
        return seg

    @property
    def current_segment(self) -> str:
        return self.history[-1][1]


@dataclass
class Account:
    account_id: str
    product_code: str
    currency_code: str
    branch_id: str
    primary_customer_id: str
    open_date: date
    opening_balance: Decimal
    monthly_fee: Decimal
    arrival_batch: str
    holders: list[tuple[str, str, int]] = field(default_factory=list)


@dataclass
class Txn:
    account_id: str
    trade_date: date
    posting_date: date
    txn_type: str
    channel: str
    amount: Decimal
    is_reversal: bool = False
    is_international: bool = False
    is_contactless: bool = False
    arrival_batch: str = ""
    txn_id: str = ""


@dataclass
class Bank:
    seed: int
    scale: int
    customers: dict[str, Customer]
    accounts: dict[str, Account]
    txns: list[Txn]
    fx: dict[tuple[str, date], Decimal]
    loan_events: list[tuple[str, str, str, str, date]]
    promotions: list[tuple[str, str, str]]
    planted: dict[str, list[str]]

    def rate(self, ccy: str, d: date) -> Decimal:
        return self.fx[(ccy, d)]


# --------------------------------------------------------------------------- build


def generate(seed: int = 42, scale: int = 10) -> Bank:
    rng = random.Random(seed)
    n_customers = 200 * scale
    fx = _fx(rng)

    customers: dict[str, Customer] = {}
    accounts: dict[str, Account] = {}
    planted: dict[str, list[str]] = {}
    acct_seq = iter(range(1, 10**7))

    def new_account(cust: Customer, product: str, opened: date, arrival: str, **kw) -> Account:
        ccy = "USD"
        if product == "SAV":
            ccy = rng.choices(("USD", "EUR", "GBP"), (70, 20, 10))[0]
        if opened < START:
            opening = {
                "CHK": money(rng.uniform(300, 8000)),
                "SAV": money(rng.uniform(1000, 40000)),
                "CARD": -money(rng.uniform(0, 3000)),
            }[product]
        else:
            opening = Decimal("0.00")
        fee = Decimal("0.00")
        if product == "CHK":
            fee = rng.choices((Decimal("0.00"), Decimal("5.00"), Decimal("12.00")), (35, 40, 25))[0]
        acct = Account(
            account_id=f"A{next(acct_seq):06d}",
            product_code=product,
            currency_code=ccy,
            branch_id=cust.home_branch_id,
            primary_customer_id=cust.customer_id,
            open_date=opened,
            opening_balance=opening,
            monthly_fee=kw.get("fee", fee),
            arrival_batch=arrival,
            holders=[(cust.customer_id, "primary", 100)],
        )
        accounts[acct.account_id] = acct
        return acct

    # Existing customers arrive in the first batch; new ones join during the period.
    n_existing = int(n_customers * 0.6)
    for i in range(1, n_customers + 1):
        branch = rng.choice(BRANCHES)[0]
        seg = rng.choices(SEGMENTS, (70, 25, 5))[0]
        if i <= n_existing:
            since = _rand_date(rng, date(2012, 1, 1), date(2024, 6, 30))
            arrival = BATCHES[0]
        else:
            since = _rand_date(rng, START, END - timedelta(days=45))
            arrival = batch_of(since)
        cust = Customer(f"C{i:05d}", branch, since, [(since, seg, arrival)])
        customers[cust.customer_id] = cust
        if i <= n_existing:
            new_account(cust, "CHK", _rand_date(rng, since, date(2024, 12, 31)), arrival)
            for product, p in (("SAV", 0.5), ("CARD", 0.35)):
                if rng.random() < p:
                    opened = _rand_date(rng, since, date(2024, 12, 31))
                    new_account(cust, product, opened, arrival)
        else:
            new_account(cust, rng.choices(("CHK", "SAV"), (70, 30))[0], since, arrival)
        held = {
            a.product_code for a in accounts.values() if a.primary_customer_id == cust.customer_id
        }
        if rng.random() < 0.2:
            options = [p for p in ("SAV", "CARD") if p not in held]
            if options:
                first_open = max(START, since + timedelta(days=20))
                if first_open < END - timedelta(days=30):
                    opened = _rand_date(rng, first_open, END - timedelta(days=30))
                    new_account(cust, rng.choice(options), opened, batch_of(opened))

    existing = [c for c in customers.values() if c.since < START]

    # Planted: inferred members. New customers whose first account transacts two
    # batches before the customer, account and holder rows are delivered.
    inferred_customers = []
    for k in range(N_INFERRED):
        opened = date(2025, 3 + k, 10 + k)
        cid = f"C{n_customers + k + 1:05d}"
        branch = BRANCHES[k % len(BRANCHES)][0]
        late = add_batches(batch_of(opened), 2)
        cust = Customer(cid, branch, opened, [(opened, "mass", late)])
        customers[cid] = cust
        new_account(cust, "CHK", opened, late, fee=Decimal("12.00"))
        inferred_customers.append(cust)
    planted["inferred_member_accounts"] = [
        a.account_id
        for a in accounts.values()
        if a.primary_customer_id in {c.customer_id for c in inferred_customers}
    ]

    # Planted: backdated corrections. Existing mass customers with a fee-paying
    # checking account, re-segmented in batch 2026-03 with effect from 2025-09-01.
    def fee_checking(c: Customer, before: date) -> bool:
        return any(
            a.primary_customer_id == c.customer_id
            and a.product_code == "CHK"
            and a.monthly_fee > 0
            and a.open_date < before
            for a in accounts.values()
        )

    correction = [c for c in existing if fee_checking(c, START)][:N_CORRECTIONS]
    for c in correction:
        c.history = [
            (c.since, "mass", BATCHES[0]),
            (CORRECTION_EFFECTIVE, "affluent", CORRECTION_BATCH),
        ]
    planted["backdated_corrections"] = [c.customer_id for c in correction]
    reserved = {c.customer_id for c in correction} | {c.customer_id for c in inferred_customers}

    # Segment changes: type 2 history for about one customer in twelve.
    candidates = [c for c in customers.values() if c.customer_id not in reserved]
    rng.shuffle(candidates)
    changers: list[Customer] = []
    for c in candidates:
        if len(changers) >= max(int(n_customers * 0.08), 16):
            break
        lo = max(START + timedelta(days=31), c.since + timedelta(days=60))
        if lo >= END - timedelta(days=15):
            continue
        eff = _rand_date(rng, lo, END - timedelta(days=15))
        if batch_of(eff) == batch_of(c.since):
            continue
        old = c.history[0][1]
        new = {
            "mass": rng.choices(("affluent", "private"), (80, 20))[0],
            "affluent": rng.choice(("mass", "private")),
            "private": "affluent",
        }[old]
        c.history.append((eff, new, batch_of(eff)))
        changers.append(c)
    planted["segment_changes"] = sorted(c.customer_id for c in changers)

    # Joint holders: about one in eight checking or savings accounts.
    pool = [c.customer_id for c in existing]
    for a in accounts.values():
        if (
            a.product_code in ("CHK", "SAV")
            and a.arrival_batch == BATCHES[0]
            and rng.random() < 0.12
        ):
            others = [x for x in rng.sample(pool, 3) if x != a.primary_customer_id]
            if rng.random() < 0.6:
                a.holders = [(a.primary_customer_id, "primary", 50), (others[0], "joint", 50)]
            else:
                a.holders = [
                    (a.primary_customer_id, "primary", 40),
                    (others[0], "joint", 30),
                    (others[1], "joint", 30),
                ]
    planted["joint_accounts"] = sorted(
        a.account_id for a in accounts.values() if len(a.holders) > 1
    )

    txns = _transactions(rng, customers, accounts)

    # Planted: late facts across a segment change. The month-end fee before a
    # customer's change arrives in the batch of the change itself.
    late_across = []
    for c in changers:
        if len(late_across) >= N_LATE_ACROSS_CHANGE:
            break
        eff = c.history[-1][0]
        prev_end = date(eff.year, eff.month, 1) - timedelta(days=1)
        if prev_end < START:
            continue
        for t in txns:
            if (
                t.txn_type == "fee"
                and t.channel == "system"
                and t.trade_date == prev_end
                and accounts[t.account_id].primary_customer_id == c.customer_id
            ):
                t.arrival_batch = batch_of(eff)
                late_across.append(c.customer_id)
                break
    planted["late_fees_across_segment_change"] = late_across

    # Random feed delays: about one fact in seventy arrives a batch or two late.
    for t in txns:
        if t.arrival_batch == batch_of(t.posting_date) and rng.random() < 0.015:
            t.arrival_batch = add_batches(t.arrival_batch, rng.choice((1, 2)))

    txns.sort(key=lambda t: (t.posting_date, t.account_id, t.trade_date, t.txn_type, t.amount))
    for i, t in enumerate(txns, 1):
        t.txn_id = f"T{i:08d}"
    planted["late_facts"] = [t.txn_id for t in txns if t.arrival_batch > batch_of(t.posting_date)]

    loan_events = _loans(rng, customers)
    promotions = [
        (b[0], p, batch)
        for batch in BATCHES
        for b in BRANCHES
        for p in rng.sample(PROMOTED_PRODUCTS, rng.choice((1, 2)))
    ]
    return Bank(seed, scale, customers, accounts, txns, fx, loan_events, promotions, planted)


def _rand_date(rng: random.Random, lo: date, hi: date) -> date:
    return lo + timedelta(days=rng.randint(0, (hi - lo).days))


def _fx(rng: random.Random) -> dict[tuple[str, date], Decimal]:
    rates: dict[tuple[str, date], Decimal] = {}
    level = {"EUR": 1.08, "GBP": 1.27}
    for d in days(START, END):
        rates[("USD", d)] = Decimal("1.000000")
        for ccy in level:
            level[ccy] *= 1 + rng.uniform(-0.003, 0.003)
            rates[(ccy, d)] = Decimal(str(level[ccy])).quantize(Decimal("0.000001"))
    return rates


def _transactions(rng, customers, accounts) -> list[Txn]:
    out: list[Txn] = []
    mult = {"mass": 1, "affluent": 3, "private": 8}

    def add(acct, trade, lag, txn_type, channel, amount, **flags):
        posting = trade + timedelta(days=lag)
        if trade < START or trade < acct.open_date or posting > END:
            return None
        t = Txn(acct.account_id, trade, posting, txn_type, channel, money(amount), **flags)
        t.arrival_batch = batch_of(posting)
        out.append(t)
        return t

    def purchase(acct, m0, m1, lo, hi, lag_lo, lag_hi):
        channel = rng.choices(("pos", "online"), (75, 25))[0]
        t = add(
            acct,
            _rand_date(rng, m0, m1),
            rng.randint(lag_lo, lag_hi),
            "purchase",
            channel,
            -rng.uniform(lo, hi),
            is_international=rng.random() < 0.05,
            is_contactless=channel == "pos" and rng.random() < 0.6,
        )
        if t is not None and rng.random() < 0.01:
            add(
                acct,
                t.posting_date + timedelta(days=rng.randint(1, 5)),
                0,
                "purchase",
                t.channel,
                -t.amount,
                is_reversal=True,
                is_international=t.is_international,
            )

    for m0 in month_starts():
        m1 = month_end(m0)
        for acct in accounts.values():
            if acct.open_date > m1:
                continue
            seg = customers[acct.primary_customer_id].segment_at(m0) or "mass"
            k = mult.get(seg, 1)
            lo = max(m0, acct.open_date)
            if acct.product_code == "CHK":
                add(
                    acct,
                    min(date(m0.year, m0.month, 25), m1),
                    0,
                    "deposit",
                    "online",
                    rng.uniform(2000, 6000) * k,
                )
                for _ in range(rng.randint(4, 10)):
                    purchase(acct, lo, m1, 5, 200, 0, 1)
                for _ in range(rng.randint(0, 2)):
                    add(
                        acct, _rand_date(rng, lo, m1), 0, "withdrawal", "atm", -rng.uniform(20, 400)
                    )
                for _ in range(rng.randint(0, 2)):
                    add(
                        acct,
                        _rand_date(rng, lo, m1),
                        0,
                        "withdrawal",
                        rng.choice(("online", "mobile")),
                        -rng.uniform(50, 1500) * k,
                    )
                if rng.random() < 0.05:
                    add(acct, _rand_date(rng, lo, m1), 0, "fee", "branch", -35)
                if acct.monthly_fee > 0:
                    add(acct, m1, 0, "fee", "system", -acct.monthly_fee)
            elif acct.product_code == "SAV":
                for _ in range(rng.randint(0, 2)):
                    add(
                        acct,
                        _rand_date(rng, lo, m1),
                        0,
                        "deposit",
                        rng.choice(("branch", "online", "mobile")),
                        rng.uniform(100, 3000) * k,
                    )
                if rng.random() < 0.3:
                    add(
                        acct,
                        _rand_date(rng, lo, m1),
                        0,
                        "withdrawal",
                        rng.choice(("branch", "online")),
                        -rng.uniform(100, 1500) * k,
                    )
                add(acct, m1, 0, "interest", "system", rng.uniform(0.5, 40) * k)
            elif acct.product_code == "CARD":
                for _ in range(rng.randint(3, 12)):
                    purchase(acct, lo, m1, 10, 500, 1, 3)
                add(
                    acct,
                    min(date(m0.year, m0.month, 15), m1),
                    0,
                    "payment",
                    rng.choice(("online", "mobile")),
                    rng.uniform(200, 2000),
                )
    return out


def _loans(rng, customers) -> list[tuple[str, str, str, str, date]]:
    events: list[tuple[str, str, str, str, date]] = []
    seq = iter(range(1, 10**6))

    def application(c: Customer, applied: date, may_reapply: bool):
        app = f"L{next(seq):05d}"
        ev = [(app, c.customer_id, c.home_branch_id, "applied", applied)]
        if rng.random() < 0.15:  # the applicant resubmits documents
            ev.append(
                (
                    app,
                    c.customer_id,
                    c.home_branch_id,
                    "applied",
                    applied + timedelta(days=rng.randint(3, 10)),
                )
            )
        decided = applied + timedelta(days=rng.randint(5, 20))
        roll = rng.random()
        if roll < 0.7:
            ev.append((app, c.customer_id, c.home_branch_id, "approved", decided))
            if rng.random() < 0.9:
                funded = decided + timedelta(days=rng.randint(3, 10))
                ev.append((app, c.customer_id, c.home_branch_id, "funded", funded))
                ev.append(
                    (
                        app,
                        c.customer_id,
                        c.home_branch_id,
                        "first_payment",
                        funded + timedelta(days=30),
                    )
                )
        elif roll < 0.9:
            ev.append((app, c.customer_id, c.home_branch_id, "declined", decided))
            if may_reapply and rng.random() < 0.3:
                application(c, decided + timedelta(days=rng.randint(30, 60)), False)
        events.extend(e for e in ev if e[4] <= END)

    for c in customers.values():
        if rng.random() < 0.06:
            application(c, _rand_date(rng, max(START, c.since), END - timedelta(days=10)), True)
    events.sort(key=lambda e: (e[4], e[0], e[3]))
    return events


# --------------------------------------------------------------------------- truth


def _fee_revenue(bank: Bank, segment_of, include) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for t in bank.txns:
        if t.txn_type != "fee" or not include(t):
            continue
        seg = segment_of(t)
        out[seg] = out.get(seg, Decimal(0)) - t.amount * bank.rate("USD", t.trade_date)
    return out


def _balances_on(bank: Bank, d: date) -> dict[str, Decimal]:
    """Local-currency balance of every account open on ``d``, as of end of day."""
    bal = {a.account_id: a.opening_balance for a in bank.accounts.values() if a.open_date <= d}
    for t in bank.txns:
        if t.posting_date <= d and t.account_id in bal:
            bal[t.account_id] += t.amount
    return bal


def _usd(bank: Bank, balances: dict[str, Decimal], d: date) -> dict[str, Decimal]:
    return {k: v * bank.rate(bank.accounts[k].currency_code, d) for k, v in balances.items()}


def ground_truth(bank: Bank) -> dict[str, dict[str, str | int]]:
    """Every figure a technique's correct.sql must return, keyed by technique."""
    accts, custs = bank.accounts, bank.customers

    def primary(t: Txn) -> Customer:
        return custs[accts[t.account_id].primary_customer_id]

    def cents(x: Decimal) -> str:
        return str(x.quantize(CENT, rounding=ROUND_HALF_UP))

    def in_year(t: Txn, y: int = 2025) -> bool:
        return t.trade_date.year == y

    dec_end = date(2025, 12, 31)
    dec = [d for d in days(date(2025, 12, 1), dec_end)]
    dec_usd = _usd(bank, _balances_on(bank, dec_end), dec_end)
    month_end_usd = sum(dec_usd.values(), Decimal(0))
    daily_totals = [sum(_usd(bank, _balances_on(bank, d), d).values(), Decimal(0)) for d in dec]
    avg_daily = sum(daily_totals, Decimal(0)) / len(daily_totals)

    as_was = _fee_revenue(bank, lambda t: primary(t).segment_at(t.trade_date), in_year)
    as_is = _fee_revenue(bank, lambda t: primary(t).current_segment, in_year)

    # Technique 01: a plan fee is an account-month fact, charged on every month an
    # account is open at month end. Checking plans are priced in USD.
    plan_fee = Decimal(0)
    for m0 in month_starts()[:12]:
        m1 = month_end(m0)
        for a in accts.values():
            if a.product_code == "CHK" and a.open_date <= m1:
                plan_fee += a.monthly_fee

    # Technique 05: the loan pipeline as of the last day of the lab.
    apps: dict[str, dict[str, date]] = {}
    for app, _c, _b, ev, d in bank.loan_events:
        apps.setdefault(app, {}).setdefault(ev, d)  # the first occurrence of each milestone
    funded = [a for a in apps.values() if "funded" in a]
    in_uw = [a for a in apps.values() if "approved" not in a and "declined" not in a]
    avg_days = Decimal(sum((a["funded"] - a["applied"]).days for a in funded)) / len(funded)

    # Technique 06: promotions with no account opened at that branch, product, month.
    openings = {(a.branch_id, a.product_code, batch_of(a.open_date)) for a in accts.values()}
    unsold = [p for p in bank.promotions if p not in openings]

    # Technique 11: what an inner join at load time would have lost.
    inferred = set(bank.planted["inferred_member_accounts"])
    early = [
        t
        for t in bank.txns
        if t.account_id in inferred and t.arrival_batch < accts[t.account_id].arrival_batch
    ]

    flags = {(t.channel, t.is_reversal, t.is_international, t.is_contactless) for t in bank.txns}

    branch_txns: dict[str, int] = {}
    branch_bal: dict[str, Decimal] = {}
    for t in bank.txns:
        if batch_of(t.trade_date) == "2025-12":
            b = accts[t.account_id].branch_id
            branch_txns[b] = branch_txns.get(b, 0) + 1
    for k, v in dec_usd.items():
        b = accts[k].branch_id
        branch_bal[b] = branch_bal.get(b, Decimal(0)) + v

    def q4(t: Txn) -> bool:
        return date(2025, 10, 1) <= t.trade_date <= dec_end

    def reported(t: Txn) -> str:
        if t.arrival_batch > AS_REPORTED_BATCH:
            return "excluded"
        return primary(t).segment_at(t.trade_date, known_by=AS_REPORTED_BATCH)

    as_reported = _fee_revenue(bank, reported, q4)
    as_reported.pop("excluded", None)
    as_effective = _fee_revenue(bank, lambda t: primary(t).segment_at(t.trade_date), q4)

    deposits = [t for t in bank.txns if t.txn_type == "deposit" and in_year(t)]

    return {
        "01": {"plan_fee_usd_2025": cents(plan_fee)},
        "02": {f"fee_revenue_usd_2025|{s}": cents(v) for s, v in sorted(as_was.items())},
        "03": {f"fee_revenue_usd_2025_as_is|{s}": cents(v) for s, v in sorted(as_is.items())},
        "04": {
            "month_end_balance_usd_2025-12": cents(month_end_usd),
            "avg_daily_balance_usd_2025-12": cents(avg_daily),
        },
        "05": {
            "in_underwriting_2026-06-30": len(in_uw),
            "funded": len(funded),
            "avg_days_applied_to_funded": cents(avg_days),
        },
        "06": {"promotions": len(bank.promotions), "promotions_without_openings": len(unsold)},
        "07": {"month_end_balance_usd_2025-12": cents(month_end_usd)},
        "08": {
            "flag_combinations_observed": len(flags),
            "flag_combinations_possible": len(CHANNELS) * 2 * 2 * 2,
        },
        "09": {
            "txn_count_2025-12": sum(1 for t in bank.txns if batch_of(t.trade_date) == "2025-12")
        },
        "10": {
            **{f"txn_count_2025-12|{b}": n for b, n in sorted(branch_txns.items())},
            **{
                f"month_end_balance_usd_2025-12|{b}": cents(v)
                for b, v in sorted(branch_bal.items())
            },
        },
        "11": {
            "late_facts": len(bank.planted["late_facts"]),
            "inferred_member_facts": len(early),
            "inferred_member_amount_usd": cents(
                sum(
                    (
                        t.amount * bank.rate(accts[t.account_id].currency_code, t.trade_date)
                        for t in early
                    ),
                    Decimal(0),
                )
            ),
        },
        "12": {
            "deposits_usd_2025": cents(
                sum(
                    (
                        t.amount * bank.rate(accts[t.account_id].currency_code, t.trade_date)
                        for t in deposits
                    ),
                    Decimal(0),
                )
            )
        },
        "13": {
            **{f"as_reported|{s}": cents(v) for s, v in sorted(as_reported.items())},
            **{f"as_effective|{s}": cents(v) for s, v in sorted(as_effective.items())},
        },
    }


# --------------------------------------------------------------------------- write


def _write(path: Path, header: list[str], rows) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write(bank: Bank, out: Path) -> dict:
    """Write the eighteen batch directories, ground_truth.json and manifest.json."""
    out.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for batch in BATCHES:
        d = out / f"batch={batch}"
        d.mkdir(exist_ok=True)
        _write(d / "branches.csv", ["branch_id", "branch_name", "city", "region"], BRANCHES)
        _write(d / "products.csv", ["product_code", "product_name", "product_category"], PRODUCTS)

        rows = []
        for c in bank.customers.values():
            city = next(b[2] for b in BRANCHES if b[0] == c.home_branch_id)
            for eff, seg, arrived in c.history:
                if arrived == batch:
                    rows.append(
                        (
                            c.customer_id,
                            f"Customer {c.customer_id[1:]}",
                            seg,
                            c.home_branch_id,
                            city,
                            c.since,
                            eff,
                        )
                    )
        ids = [r[0] for r in rows]
        assert len(ids) == len(set(ids)), f"two customer rows in one batch: {batch}"
        _write(
            d / "customers.csv",
            [
                "customer_id",
                "full_name",
                "segment",
                "home_branch_id",
                "city",
                "customer_since",
                "effective_date",
            ],
            rows,
        )

        arriving = [a for a in bank.accounts.values() if a.arrival_batch == batch]
        _write(
            d / "accounts.csv",
            [
                "account_id",
                "product_code",
                "currency_code",
                "branch_id",
                "primary_customer_id",
                "open_date",
                "opening_balance",
                "monthly_fee",
            ],
            [
                (
                    a.account_id,
                    a.product_code,
                    a.currency_code,
                    a.branch_id,
                    a.primary_customer_id,
                    a.open_date,
                    a.opening_balance,
                    a.monthly_fee,
                )
                for a in arriving
            ],
        )
        _write(
            d / "account_holders.csv",
            ["account_id", "customer_id", "holder_role", "ownership_pct"],
            [(a.account_id, *h) for a in arriving for h in a.holders],
        )

        tx = [t for t in bank.txns if t.arrival_batch == batch]
        counts[batch] = len(tx)
        _write(
            d / "transactions.csv",
            [
                "txn_id",
                "account_id",
                "trade_date",
                "posting_date",
                "txn_type",
                "channel",
                "is_reversal",
                "is_international",
                "is_contactless",
                "currency_code",
                "amount",
            ],
            [
                (
                    t.txn_id,
                    t.account_id,
                    t.trade_date,
                    t.posting_date,
                    t.txn_type,
                    t.channel,
                    t.is_reversal,
                    t.is_international,
                    t.is_contactless,
                    bank.accounts[t.account_id].currency_code,
                    t.amount,
                )
                for t in tx
            ],
        )

        m0 = date(int(batch[:4]), int(batch[5:]), 1)
        _write(
            d / "fx_rates.csv",
            ["currency_code", "rate_date", "usd_per_unit"],
            [
                (ccy, dd, bank.fx[(ccy, dd)])
                for dd in days(m0, month_end(m0))
                for ccy in ("USD", "EUR", "GBP")
            ],
        )
        _write(
            d / "loan_events.csv",
            ["application_id", "customer_id", "branch_id", "event_type", "event_date"],
            [e for e in bank.loan_events if batch_of(e[4]) == batch],
        )
        _write(
            d / "promotions.csv",
            ["branch_id", "product_code", "promo_month"],
            [p for p in bank.promotions if p[2] == batch],
        )

    truth = ground_truth(bank)
    (out / "ground_truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    manifest = {
        "seed": bank.seed,
        "scale": bank.scale,
        "batches": BATCHES,
        "customers": len(bank.customers),
        "accounts": len(bank.accounts),
        "transactions": len(bank.txns),
        "transactions_per_batch": counts,
        "loan_events": len(bank.loan_events),
        "promotions": len(bank.promotions),
        "planted": {
            **{k: v for k, v in bank.planted.items() if k != "late_facts"},
            "late_facts": len(bank.planted["late_facts"]),
            "backdated_correction": {
                "effective": CORRECTION_EFFECTIVE.isoformat(),
                "delivered_in_batch": CORRECTION_BATCH,
            },
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
