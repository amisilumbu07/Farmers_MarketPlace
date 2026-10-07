"use client";

import { FormEvent, useEffect, useState } from "react";

type Lot = { id: string; product: string; quantity_kg: number; price_per_kg: number; farmer_id: string; active?: boolean };
type Allocation = { lot_id: string; farmer_id: string; quantity_kg: number; price_per_kg: number; distance_km: number; score: number; distance_score: number; price_score: number; fulfilment_risk: number };
type MatchPlan = { requested_quantity_kg: number; allocated_quantity_kg: number; complete: boolean; allocations: Allocation[] };
type Farm = { id: string; farmer_id: string; name: string; latitude: number; longitude: number };
type Order = { id: string; buyer_id: string; lot_id: string; quantity_kg: number; status: string; pool_id?: string | null };
type Session = { token: string; user_id: string; role: string; request_id?: string; order_id?: string; farm?: Farm };
type Pool = { id: string; status: string; total_kg: number; separate_cost: number; pooled_cost: number; savings: number; savings_pct: number; route_km: number; vehicle_id: string | null; stops: { seq: number; kind: string; order_id: string }[]; quotes: { id: string; vehicle_id: string; cost: number }[] };
type Attestation = { id: string; type: string; actor_id: string; evidence_url: string | null; evidence_hash: string | null; created_at: string };
type History = { attestations: Attestation[]; dispute: Dispute | null };
type Dispute = { id: string; order_id: string; opened_by: string; reason: string; status: string; resolution: string | null };
type Reputation = { score: number; points: number; events: Record<string, number> };
type AdminUser = { id: string; email: string; role: string; active: boolean };

const KNOWN = ["tomatoes", "apples", "oranges", "mangoes", "peppers", "potatoes", "onions", "cabbage", "carrots", "bananas", "maize", "lettuce", "spinach"];
const productImage = (name: string) => {
  const k = name.toLowerCase().trim().replace(/s$/, "");
  return `/products/${KNOWN.find((n) => n.replace(/s$/, "") === k) ?? "default"}.svg`;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function api<T>(path: string, options: RequestInit = {}, token = ""): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? `Request failed (${response.status})`);
  return data as T;
}

const Logo = () => <svg viewBox="0 0 40 40" width="32" height="32" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="#19764a" opacity=".12" /><path d="M20 10l4 5h-2v7h-4v-7h-2z" fill="#19764a" /><path d="M26 18c1.1 0 2 .9 2 2v8c0 1.1-.9 2-2 2H14c-1.1 0-2-.9-2-2v-8c0-1.1.9-2 2-2" fill="#ff9500" opacity=".7" /></svg>;

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [token, setToken] = useState("");
  const [lots, setLots] = useState<Lot[]>([]);
  const [plan, setPlan] = useState<MatchPlan | null>(null);
  const [requestId, setRequestId] = useState("");
  const [lotId, setLotId] = useState("");
  const [orderQuantity, setOrderQuantity] = useState("20");
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [adminLots, setAdminLots] = useState<Lot[]>([]);
  const [pools, setPools] = useState<Pool[]>([]);
  const [history, setHistory] = useState<Record<string, History>>({});
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [reputation, setReputation] = useState<Reputation | null>(null);
  const [query, setQuery] = useState("");
  const [disputeReason, setDisputeReason] = useState("Quality problem");

  const report = (text: string, isError = false) => { setMessage(text); setError(isError); };
  const loadLots = async () => { try { const nextLots = await api<Lot[]>("/products"); setLots(nextLots); if (!nextLots.length && !session) report("API connected. Load demo data to populate sample listings."); } catch (e) { report(`API connection failed: ${(e as Error).message}`, true); } };
  useEffect(() => { loadLots(); }, []);

  const loadFarmerDashboard = async (farmerToken: string, fallbackFarm?: Farm) => {
    const [nextFarms, nextOrders] = await Promise.all([
      api<Farm[]>("/farms", {}, farmerToken),
      api<Order[]>("/orders", {}, farmerToken),
    ]);
    setFarms(nextFarms.length ? nextFarms : fallbackFarm ? [fallbackFarm] : []); setOrders(nextOrders);
  };

  const loadAdminDashboard = async (adminToken: string) => {
    const [nextUsers, nextLots, nextOrders] = await Promise.all([
      api<AdminUser[]>("/admin/users", {}, adminToken),
      api<Lot[]>("/admin/lots", {}, adminToken),
      api<Order[]>("/admin/orders", {}, adminToken),
    ]);
    setUsers(nextUsers); setAdminLots(nextLots); setOrders(nextOrders); setDisputes(await api<Dispute[]>("/disputes", {}, adminToken));
  };

  const loadReputation = async (authToken: string, userId: string) => setReputation(await api<Reputation>(`/users/${userId}/reputation`, {}, authToken));
  const showHistory = async (orderId: string) => {
    try { const h = await api<History>(`/orders/${orderId}/history`, {}, token); setHistory((current) => ({ ...current, [orderId]: h })); }
    catch (e) { report((e as Error).message, true); }
  };
  const openDispute = async (orderId: string) => {
    try { await api(`/orders/${orderId}/dispute`, { method: "POST", body: JSON.stringify({ reason: disputeReason }) }, token); await moveOrder(orderId, null); report(`Dispute opened on ${orderId}.`); }
    catch (e) { report((e as Error).message, true); }
  };
  const resolveDispute = async (dispute: Dispute, outcome: "refund" | "complete") => {
    try { await api(`/disputes/${dispute.id}/resolve`, { method: "POST", body: JSON.stringify({ outcome }) }, token); await loadAdminDashboard(token); report(`Dispute ${dispute.id} resolved: ${outcome}.`); }
    catch (e) { report((e as Error).message, true); }
  };
  const loadPools = async (authToken: string) => setPools(await api<Pool[]>("/transport-pools", {}, authToken));
  const proposePools = async () => {
    try { const found = await api<Pool[]>("/transport-pools/propose", { method: "POST" }, token); await loadPools(token); report(found.length ? `${found.length} pool(s) proposed.` : "No new pools: nothing compatible or savings too small."); }
    catch (e) { report((e as Error).message, true); }
  };
  const confirmPool = async (pool: Pool, quoteId: string) => {
    try { await api(`/transport-pools/${pool.id}/confirm`, { method: "POST", body: JSON.stringify({ quote_id: quoteId }) }, token); await loadPools(token); await loadTransporterOrders(token); report(`Pool ${pool.id} confirmed.`); }
    catch (e) { report((e as Error).message, true); }
  };
  const dissolvePool = async (pool: Pool) => {
    try { await api(`/transport-pools/${pool.id}/dissolve`, { method: "POST" }, token); await loadPools(token); await loadTransporterOrders(token); report(`Pool ${pool.id} dissolved. Its orders can be pooled again.`); }
    catch (e) { report((e as Error).message, true); }
  };
  const loadTransporterOrders = async (authToken: string) => setOrders(await api<Order[]>("/orders", {}, authToken));
  const moveOrder = async (orderId: string, step: "ready" | "pickup" | "deliver" | "complete" | "cancel" | null) => {
    try { if (step) await api(`/orders/${orderId}/${step}`, { method: "POST" }, token); setHistory((current) => { const { [orderId]: _gone, ...rest } = current; return rest; }); if (session) loadReputation(token, session.user_id); if (session?.role === "farmer") await loadFarmerDashboard(token); else if (session?.role === "transporter") { await loadTransporterOrders(token); await loadPools(token); } else setOrders(await api<Order[]>("/orders", {}, token)); if (step) report(`Order ${orderId}: ${step} done.`); }
    catch (e) { report((e as Error).message, true); }
  };

  const loadDemo = async (role: "buyer" | "farmer" | "admin" | "transporter") => {
    try {
      const demo = await api<Session>(`/demo/seed?role=${role}`, { method: "POST" });
      setToken(demo.token); setSession(demo); setHistory({}); loadReputation(demo.token, demo.user_id).catch(() => setReputation(null)); setRequestId(demo.request_id ?? ""); setPlan(null);
      if (role !== "admin") { setUsers([]); setAdminLots([]); }
      if (role === "farmer") await loadFarmerDashboard(demo.token, demo.farm);
      else if (role === "admin") await loadAdminDashboard(demo.token);
      else if (role === "transporter") { await loadPools(demo.token); await loadTransporterOrders(demo.token); }
      else { setFarms([]); setUsers([]); setOrders(await api<Order[]>("/orders", {}, demo.token)); }
      if (role !== "transporter") setPools([]);
      report(`Demo data loaded. You are signed in as the ${role}.`); await loadLots();
    } catch (e) { report((e as Error).message, true); }
  };

  const acceptOrder = async (orderId: string) => {
    try { await api(`/orders/${orderId}/accept`, { method: "POST" }, token); await loadFarmerDashboard(token); report(`Order ${orderId} accepted.`); }
    catch (e) { report((e as Error).message, true); }
  };

  const openRequest = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const request = await api<{ id: string }>("/buyer-requests", { method: "POST", body: JSON.stringify({ product: data.product, quantity_kg: Number(data.quantity), max_price_per_kg: data.max_price ? Number(data.max_price) : null, latitude: Number(data.latitude), longitude: Number(data.longitude), radius_km: Number(data.radius) }) }, token);
      setRequestId(request.id); report(`Buyer request opened: ${request.id}`);
    } catch (e) { report((e as Error).message, true); }
  };

  const findMatches = async () => {
    try { setPlan(await api<MatchPlan>(`/buyer-requests/${requestId}/matches`, {}, token)); report("Match plan calculated. Inventory has not changed."); }
    catch (e) { report((e as Error).message, true); }
  };

  const createGroupedOrder = async () => {
    try {
      const result = await api<{ group_id: string; orders: Order[] }>(`/buyer-requests/${requestId}/orders`, { method: "POST" }, token);
      setPlan(null); await loadLots(); report(`Grouped order ${result.group_id} created with ${result.orders.length} farmer orders.`);
    } catch (e) { report((e as Error).message, true); }
  };

  const toggleUser = async (user: AdminUser) => {
    try {
      await api(`/admin/users/${user.id}`, { method: "PATCH", body: JSON.stringify({ active: !user.active }) }, token);
      await loadAdminDashboard(token); report(`${user.email} ${user.active ? "disabled" : "enabled"}.`);
    } catch (e) { report((e as Error).message, true); }
  };

  const toggleLot = async (lot: Lot) => {
    try {
      await api(`/admin/lots/${lot.id}`, { method: "PATCH", body: JSON.stringify({ active: !lot.active }) }, token);
      await loadAdminDashboard(token); await loadLots(); report(`${lot.id} ${lot.active ? "deactivated" : "activated"}.`);
    } catch (e) { report((e as Error).message, true); }
  };

  const createOrder = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try { const order = await api<{ id: string; status: string }>("/orders", { method: "POST", body: JSON.stringify({ lot_id: lotId, quantity_kg: Number(orderQuantity) }) }, token); setPlan(null); report(`Order ${order.id} created: ${order.status}. Recalculate matches for current stock.`); await loadLots(); }
    catch (e) { report((e as Error).message, true); }
  };

  const signOut = () => { setSession(null); setToken(""); setPlan(null); setFarms([]); setOrders([]); setUsers([]); setAdminLots([]); report("Signed out."); };
  const shown = lots.filter((lot) => lot.product.toLowerCase().includes(query.toLowerCase()));
  const pickLot = (lot: Lot) => {
    setLotId(lot.id); report(session?.role === "buyer" ? `Lot ${lot.id} selected. Enter a quantity under Create direct order.` : "Log in as a buyer to order a lot.");
    document.getElementById("lotId")?.scrollIntoView({ behavior: "smooth" });
  };

  return <div className="shell">
    <header className="topbar">
      <div className="topbar-row">
        <a className="logo" href="/" aria-label="AgriLink home"><Logo /><span>AgriLink</span></a>
      </div>
      <div className="search"><input type="search" aria-label="Search produce" placeholder="Search produce, e.g. tomatoes" value={query} onChange={(e) => setQuery(e.target.value)} /></div>
    </header>
    <main className="content">
      <div className={`status${error ? " error" : ""}`} role="status" aria-live="polite">{message}</div>
      <div className="toolbar"><div>{session ? <span className="pill">{session.role} - {session.user_id}{reputation ? ` - reputation ${reputation.score}` : ""}</span> : <p>Choose a demo role to test the marketplace.</p>}</div><div className="actions"><button onClick={() => loadDemo("buyer")}>Buyer demo</button><button className="secondary" onClick={() => loadDemo("farmer")}>Farmer demo</button><button className="secondary" onClick={() => loadDemo("admin")}>Admin demo</button><button className="secondary" onClick={() => loadDemo("transporter")}>Transporter demo</button>{session && <button className="secondary" onClick={signOut}>Sign out</button>}</div></div>
      <section className="produce">
        <h2 className="section-title">Available produce</h2><p className="muted">Active farmer lots. Choose one to test a direct order.</p>
        {shown.length ? <div className="product-grid">{shown.map((lot) => <article className="product-card" key={lot.id}><img src={productImage(lot.product)} alt={lot.product} loading="lazy" /><div className="product-info"><h3>{lot.product}</h3><p className="muted">{lot.quantity_kg} kg at {lot.price_per_kg.toFixed(2)}/kg</p><p className="muted lot-id">{lot.id}</p><button onClick={() => pickLot(lot)}>{lotId === lot.id ? "Selected" : "Use lot"}</button></div></article>)}</div> : <p className="empty">{lots.length ? "No produce matches your search." : "No active listings."}</p>}
      </section>
      <div className="grid">
        {session?.role === "buyer" && <section className="card"><h2>Open buyer request</h2><p className="muted">Describe demand before it is matched to farmer supply.</p><form onSubmit={openRequest}><div className="form-grid"><div><label htmlFor="product">Product</label><input id="product" name="product" required defaultValue="Tomatoes" /></div><div><label htmlFor="quantity">Quantity (kg)</label><input id="quantity" name="quantity" type="number" min=".01" step=".01" required defaultValue="100" /></div><div><label htmlFor="max_price">Max price/kg</label><input id="max_price" name="max_price" type="number" min=".01" step=".01" defaultValue="0.80" /></div><div><label htmlFor="radius">Search radius (km)</label><input id="radius" name="radius" type="number" min="1" max="500" required defaultValue="50" /></div><div><label htmlFor="latitude">Pickup latitude</label><input id="latitude" name="latitude" type="number" step="any" required defaultValue="1.30" /></div><div><label htmlFor="longitude">Pickup longitude</label><input id="longitude" name="longitude" type="number" step="any" required defaultValue="36.82" /></div></div><div className="actions"><button>Open request</button></div></form><label htmlFor="requestId">Request ID</label><input id="requestId" value={requestId} onChange={(event) => setRequestId(event.target.value)} placeholder="req_..." /><div className="actions"><button className="secondary" type="button" onClick={findMatches} disabled={!requestId}>Find nearby supply</button></div></section>}
        {session?.role === "buyer" && <section className="card"><h2>Match plan</h2>{plan ? <><p className="pill">{plan.complete ? "Complete match" : "Partial match"}</p><p>{plan.allocated_quantity_kg} of {plan.requested_quantity_kg} kg allocated{plan.complete ? "" : ` - short by ${(plan.requested_quantity_kg - plan.allocated_quantity_kg).toFixed(2)} kg. Widen the radius or raise the max price.`}</p>{plan.allocations.map((allocation, index) => <div className="match" key={allocation.lot_id}><strong>#{index + 1} {allocation.quantity_kg} kg from {allocation.lot_id}</strong><div className="muted">Farmer {allocation.farmer_id} · {allocation.distance_km} km · {allocation.price_per_kg.toFixed(2)}/kg · cost {(allocation.quantity_kg * allocation.price_per_kg).toFixed(2)}<br />Score {allocation.score.toFixed(3)} = distance {allocation.distance_score.toFixed(2)} (50%) + price {allocation.price_score.toFixed(2)} (30%) + risk {allocation.fulfilment_risk.toFixed(2)} (20%). Lower is better.</div></div>)}<p><strong>Total: {plan.allocations.reduce((sum, a) => sum + a.quantity_kg * a.price_per_kg, 0).toFixed(2)}</strong></p>{plan.complete && <div className="actions"><button onClick={createGroupedOrder}>Create grouped order</button></div>}</> : <p className="empty">Open a request, then calculate its match plan.</p>}</section>}
        {session?.role === "buyer" && <section className="card"><h2>Create direct order</h2><p className="muted">This reserves quantity from one selected lot.</p><form onSubmit={createOrder}><label htmlFor="lotId">Lot ID</label><input id="lotId" value={lotId} onChange={(event) => setLotId(event.target.value)} required placeholder="lot_..." /><label htmlFor="orderQuantity">Quantity (kg)</label><input id="orderQuantity" value={orderQuantity} onChange={(event) => setOrderQuantity(event.target.value)} type="number" min=".01" step=".01" required /><div className="actions"><button>Create order</button></div></form></section>}
        {session?.role === "buyer" && <section className="card wide"><h2>My orders</h2><p className="muted">Confirm receipt once delivered, or open a dispute while an order is in transit or delivered. Each confirmation is recorded with who and when.</p><label htmlFor="disputeReason">Dispute reason</label><input id="disputeReason" value={disputeReason} onChange={(event) => setDisputeReason(event.target.value)} />{orders.length ? orders.map((order) => <article className="order-row" key={order.id}><header><strong>{order.id}</strong><span className="pill">{order.status}</span></header><div className="muted">{order.quantity_kg} kg from {order.lot_id}</div><div className="actions">{order.status === "DELIVERED" && <button onClick={() => moveOrder(order.id, "complete")}>Confirm receipt</button>}{(order.status === "IN_TRANSIT" || order.status === "DELIVERED") && <button className="secondary" onClick={() => openDispute(order.id)}>Open dispute</button>}{["PENDING", "ACCEPTED", "READY_FOR_PICKUP"].includes(order.status) && <button className="secondary" onClick={() => moveOrder(order.id, "cancel")}>Cancel order</button>}<button className="secondary" onClick={() => showHistory(order.id)}>History</button></div>{history[order.id] && <div className="muted">{history[order.id].attestations.length ? history[order.id].attestations.map((a) => <div key={a.id}>{a.type.replace("_", " ").toLowerCase()} by {a.actor_id} at {new Date(a.created_at).toLocaleString()}{a.evidence_hash ? ` - evidence ${a.evidence_hash.slice(0, 10)}...` : ""}</div>) : "No confirmations yet."}{history[order.id].dispute && <div>Dispute {history[order.id].dispute!.status.toLowerCase()}: {history[order.id].dispute!.reason}{history[order.id].dispute!.resolution ? ` (${history[order.id].dispute!.resolution})` : ""}</div>}</div>}</article>) : <p className="empty">No orders yet.</p>}</section>}
        {session?.role === "farmer" && <section className="card"><h2>Farmer order queue</h2><p className="muted">Orders shown here belong to this farmer's produce lots.</p>{orders.length ? orders.map((order) => <article className="order-row" key={order.id}><header><strong>{order.id}</strong><span className="pill">{order.status}</span></header><div className="muted">{order.quantity_kg} kg from {order.lot_id}<br />Buyer: {order.buyer_id}</div>{order.status === "PENDING" && <button onClick={() => acceptOrder(order.id)}>Accept order</button>}{order.status === "ACCEPTED" && <button onClick={() => moveOrder(order.id, "ready")}>Mark ready for pickup</button>}</article>) : <p className="empty">No orders assigned to your lots.</p>}</section>}
        {session?.role === "farmer" && farms[0] && <section className="card"><h2>Farm location</h2><p><strong>{farms[0].name}</strong><br /><span className="muted">{farms[0].latitude}, {farms[0].longitude}</span></p><iframe className="map-frame" title={`${farms[0].name} on Google Maps`} loading="lazy" src={`https://www.google.com/maps?q=${farms[0].latitude},${farms[0].longitude}&z=13&output=embed`} /><a className="map-link" href={`https://www.google.com/maps?q=${farms[0].latitude},${farms[0].longitude}`} target="_blank" rel="noreferrer">Open in Google Maps</a></section>}
        {session?.role === "transporter" && <section className="card wide"><h2>Pooled transport</h2><p className="muted">Compatible accepted orders (same destination area, delivery window, nearby pickups, within vehicle capacity) can share one truck.</p><div className="actions"><button onClick={proposePools}>Find pools</button></div>{pools.length ? pools.map((pool) => <article className="order-row" key={pool.id}><header><strong>{pool.id}</strong><span className="pill">{pool.status}</span></header><div className="muted">{pool.total_kg} kg · {pool.route_km} km route<br />Separate delivery {pool.separate_cost.toFixed(2)} vs pooled {pool.pooled_cost.toFixed(2)} - saves <strong>{pool.savings.toFixed(2)} ({pool.savings_pct}%)</strong><br />{pool.stops.map((stop) => `${stop.seq + 1}. ${stop.kind} ${stop.order_id}`).join(" → ")}</div>{pool.status === "PROPOSED" && <div className="actions"><button className="secondary" onClick={() => dissolvePool(pool)}>Dissolve pool</button></div>}{pool.status === "PROPOSED" && (pool.quotes.length ? pool.quotes.map((quote) => <div className="actions" key={quote.id}><span>{quote.vehicle_id}: {quote.cost.toFixed(2)}</span><button onClick={() => confirmPool(pool, quote.id)}>Confirm with this vehicle</button></div>) : <p className="empty">No registered vehicle fits this load.</p>)}</article>) : <p className="empty">No pools yet.</p>}</section>}
        {session?.role === "transporter" && <section className="card wide"><h2>Shipment orders</h2>{orders.filter((order) => order.pool_id).map((order) => <div className="listing" key={order.id}><div><strong>{order.id}</strong><span className="muted">{order.quantity_kg} kg · {order.status} · {order.pool_id}</span></div>{order.status === "READY_FOR_PICKUP" && <button onClick={() => moveOrder(order.id, "pickup")}>Confirm pickup</button>}{order.status === "IN_TRANSIT" && <button onClick={() => moveOrder(order.id, "deliver")}>Confirm delivery</button>}</div>)}{!orders.some((order) => order.pool_id) && <p className="empty">No pooled orders yet.</p>}</section>}
        {session?.role === "admin" && <section className="card wide"><h2>Disputes</h2>{disputes.length ? disputes.map((dispute) => <div className="listing" key={dispute.id}><div><strong>{dispute.order_id}</strong><span className="muted">{dispute.reason} · {dispute.status}{dispute.resolution ? ` (${dispute.resolution})` : ""} · opened by {dispute.opened_by}</span></div>{dispute.status === "OPEN" && <div className="actions"><button onClick={() => resolveDispute(dispute, "refund")}>Refund buyer</button><button className="secondary" onClick={() => resolveDispute(dispute, "complete")}>Complete order</button></div>}</div>) : <p className="empty">No disputes.</p>}</section>}
        {session?.role === "admin" && <section className="card wide"><h2>User moderation</h2>{users.map((user) => <div className="listing" key={user.id}><div><strong>{user.email}</strong><span className="muted">{user.role} · {user.active ? "active" : "disabled"}</span></div><button className="secondary" disabled={user.id === session.user_id} onClick={() => toggleUser(user)}>{user.id === session.user_id ? "Current admin" : user.active ? "Disable" : "Enable"}</button></div>)}</section>}
        {session?.role === "admin" && <section className="card wide"><h2>Listing moderation</h2>{adminLots.map((lot) => <div className="listing" key={lot.id}><div><strong>{lot.product}</strong><span className="muted">{lot.quantity_kg} kg · {lot.active ? "active" : "inactive"} · {lot.id}</span></div><button className="secondary" onClick={() => toggleLot(lot)}>{lot.active ? "Deactivate" : "Activate"}</button></div>)}</section>}
        {session?.role === "admin" && <section className="card wide"><h2>All orders</h2>{orders.map((order) => <div className="order-row" key={order.id}><strong>{order.id}</strong><div className="muted">{order.quantity_kg} kg · {order.status} · {order.lot_id}</div></div>)}</section>}
      </div>
    </main>
  </div>;
}
