// Starter model: the race between an external confirmation and the expiry of a hold,
// written only in the shared roles. One resource, two customers.
//
// The naive design issues an entitlement as soon as the confirmation succeeds.
// The guarded design issues it only while the customer still holds the resource.
module starter {
  const GUARDED: bool

  pure val Customers = Set("c1", "c2")

  var stopped: bool            // the emergency stop is in effect
  var holder: str              // who holds the resource; "" when nobody does
  var confirming: Set[str]     // customers waiting for the external confirmation
  var entitled: Set[str]       // customers who received the entitlement
  var orphaned: Set[str]       // confirmed, but neither entitled nor refunded

  action init = all {
    stopped' = false, holder' = "", confirming' = Set(), entitled' = Set(), orphaned' = Set(),
  }

  action hold(c: str): bool = all {
    not(stopped), holder == "", not(c.in(confirming)), not(c.in(entitled)),
    holder' = c,
    stopped' = stopped, confirming' = confirming, entitled' = entitled, orphaned' = orphaned,
  }

  action startConfirmation(c: str): bool = all {
    not(stopped), holder == c, not(c.in(confirming)), not(c.in(entitled)),
    confirming' = confirming.union(Set(c)),
    stopped' = stopped, holder' = holder, entitled' = entitled, orphaned' = orphaned,
  }

  // A hold expires unless its holder already received the entitlement.
  action holdExpires = all {
    holder != "", not(holder.in(entitled)),
    holder' = "",
    stopped' = stopped, confirming' = confirming, entitled' = entitled, orphaned' = orphaned,
  }

  // The external confirmation arrives whether or not the system is stopped.
  action confirmationSucceeds(c: str): bool = all {
    c.in(confirming),
    confirming' = confirming.exclude(Set(c)),
    entitled' = if (not(GUARDED) or holder == c) entitled.union(Set(c)) else entitled,
    orphaned' = if (GUARDED and holder != c) orphaned.union(Set(c)) else orphaned,
    stopped' = stopped, holder' = holder,
  }

  action emergencyStop = all {
    not(stopped),
    stopped' = true,
    holder' = holder, confirming' = confirming, entitled' = entitled, orphaned' = orphaned,
  }

  action step = any {
    nondet c = Customers.oneOf()
    any { hold(c), startConfirmation(c), confirmationSucceeds(c) },
    holdExpires, emergencyStop,
  }

  // At most one customer is entitled to the resource.
  val exclusive = entitled.size() <= 1

  // No confirmed customer is left with nothing.
  val noOrphan = orphaned.size() == 0
}

module naive {
  import starter(GUARDED = false).*

  // The hold of c1 expires while c1 waits; c2 takes the resource; both confirmations succeed.
  run doubleEntitlementTest =
    init.then(hold("c1")).then(startConfirmation("c1")).then(holdExpires)
      .then(hold("c2")).then(startConfirmation("c2"))
      .then(confirmationSucceeds("c1")).then(confirmationSucceeds("c2"))
      .expect(entitled.size() == 2)
}

module guarded {
  import starter(GUARDED = true).*
}
