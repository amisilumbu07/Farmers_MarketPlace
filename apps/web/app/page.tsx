"use client";

import { FormEvent, useEffect, useState } from "react";

type Lot = { id: string; product: string; quantity_kg: number; price_per_kg: number; farmer_id: string; active?: boolean };
type Allocation = { lot_id: string; farmer_id: string; quantity_kg: number; price_per_kg: number; distance_km: number; score: number; distance_score: number; price_score: number; fulfilment_risk: number };
type MatchPlan = { requested_quantity_kg: number; allocated_quantity_kg: number; complete: boolean; allocations: Allocation[] };
type Farm = { id: string; farmer_id: string; name: string; latitude: number; longitude: number };
type Order = { id: string; buyer_id: string; lot_id: string; quantity_kg: number; status: string };
type Session = { token: string; user_id: string; role: string; request_id?: string; order_id?: string; farm?: Farm };
type AdminUser = { id: string; email: string; role: string; active: boolean };

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
    setUsers(nextUsers); setAdminLots(nextLots); setOrders(nextOrders);
  };

  const loadDemo = async (role: "buyer" | "farmer" | "admin") => {
    try {
      const demo = await api<Session>(`/demo/seed?role=${role}`, { method: "POST" });
      setToken(demo.token); setSession(demo); setRequestId(demo.request_id ?? ""); setPlan(null);
      if (role !== "admin") { setUsers([]); setAdminLots([]); }
      if (role === "farmer") await loadFarmerDashboard(demo.token, demo.farm);
      else if (role === "admin") await loadAdminDashboard(demo.token);
      else { setFarms([]); setOrders([]); setUsers([]); }
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

  return <div className="shell">
    <header className="hero"><h1>Harvest Hub</h1><p>Phase 2 supply matching for farmers and buyers.</p></header>
    <main className="content">
      <div className="toolbar"><div>{session ? <span className="pill">{session.role} - {session.user_id}</span> : <p>Choose a demo role to test the marketplace.</p>}</div><div className="actions"><button onClick={() => loadDemo("buyer")}>Buyer demo</button><button className="secondary" onClick={() => loadDemo("farmer")}>Farmer demo</button><button className="secondary" onClick={() => loadDemo("admin")}>Admin demo</button>{session && <button className="secondary" onClick={() => { setSession(null); setToken(""); setPlan(null); setFarms([]); setOrders([]); setUsers([]); setAdminLots([]); report("Signed out."); }}>Sign out</button>}</div></div>
      <div className={`status${error ? " error" : ""}`} role="status" aria-live="polite">{message}</div>
      <div className="grid">
        <section className="card wide"><h2>Available produce</h2><p className="muted">Active farmer lots. Choose one to test a direct order.</p>{lots.length ? lots.map((lot) => <div className="listing" key={lot.id}><div><strong>{lot.product}</strong><span className="muted">{lot.quantity_kg} kg at {lot.price_per_kg.toFixed(2)}/kg - {lot.id}</span></div><button onClick={() => setLotId(lot.id)}>Use lot</button></div>) : <p className="empty">No active listings.</p>}</section>
        {session?.role === "buyer" && <section className="card"><h2>Open buyer request</h2><p className="muted">Describe demand before it is matched to farmer supply.</p><form onSubmit={openRequest}><div className="form-grid"><div><label htmlFor="product">Product</label><input id="product" name="product" required defaultValue="Tomatoes" /></div><div><label htmlFor="quantity">Quantity (kg)</label><input id="quantity" name="quantity" type="number" min=".01" step=".01" required defaultValue="100" /></div><div><label htmlFor="max_price">Max price/kg</label><input id="max_price" name="max_price" type="number" min=".01" step=".01" defaultValue="0.80" /></div><div><label htmlFor="radius">Search radius (km)</label><input id="radius" name="radius" type="number" min="1" max="500" required defaultValue="50" /></div><div><label htmlFor="latitude">Pickup latitude</label><input id="latitude" name="latitude" type="number" step="any" required defaultValue="1.30" /></div><div><label htmlFor="longitude">Pickup longitude</label><input id="longitude" name="longitude" type="number" step="any" required defaultValue="36.82" /></div></div><div className="actions"><button>Open request</button></div></form><label htmlFor="requestId">Request ID</label><input id="requestId" value={requestId} onChange={(event) => setRequestId(event.target.value)} placeholder="req_..." /><div className="actions"><button className="secondary" type="button" onClick={findMatches} disabled={!requestId}>Find nearby supply</button></div></section>}
        {session?.role === "buyer" && <section className="card"><h2>Match plan</h2>{plan ? <><p className="pill">{plan.complete ? "Complete match" : "Partial match"}</p><p>{plan.allocated_quantity_kg} of {plan.requested_quantity_kg} kg allocated.</p>{plan.allocations.map((allocation) => <div className="match" key={allocation.lot_id}><strong>{allocation.quantity_kg} kg from {allocation.lot_id}</strong><div className="muted">{allocation.distance_km} km away · {allocation.price_per_kg.toFixed(2)}/kg · score {allocation.score.toFixed(3)}</div></div>)}{plan.complete && <div className="actions"><button onClick={createGroupedOrder}>Create grouped order</button></div>}</> : <p className="empty">Open a request, then calculate its match plan.</p>}</section>}
        {session?.role === "buyer" && <section className="card"><h2>Create direct order</h2><p className="muted">This reserves quantity from one selected lot.</p><form onSubmit={createOrder}><label htmlFor="lotId">Lot ID</label><input id="lotId" value={lotId} onChange={(event) => setLotId(event.target.value)} required placeholder="lot_..." /><label htmlFor="orderQuantity">Quantity (kg)</label><input id="orderQuantity" value={orderQuantity} onChange={(event) => setOrderQuantity(event.target.value)} type="number" min=".01" step=".01" required /><div className="actions"><button>Create order</button></div></form></section>}
        {session?.role === "farmer" && <section className="card"><h2>Farmer order queue</h2><p className="muted">Orders shown here belong to this farmer's produce lots.</p>{orders.length ? orders.map((order) => <article className="order-row" key={order.id}><header><strong>{order.id}</strong><span className="pill">{order.status}</span></header><div className="muted">{order.quantity_kg} kg from {order.lot_id}<br />Buyer: {order.buyer_id}</div>{order.status === "PENDING" && <button onClick={() => acceptOrder(order.id)}>Accept order</button>}</article>) : <p className="empty">No orders assigned to your lots.</p>}</section>}
        {session?.role === "farmer" && farms[0] && <section className="card"><h2>Farm location</h2><p><strong>{farms[0].name}</strong><br /><span className="muted">{farms[0].latitude}, {farms[0].longitude}</span></p><iframe className="map-frame" title={`${farms[0].name} on Google Maps`} loading="lazy" src={`https://www.google.com/maps?q=${farms[0].latitude},${farms[0].longitude}&z=13&output=embed`} /><a className="map-link" href={`https://www.google.com/maps?q=${farms[0].latitude},${farms[0].longitude}`} target="_blank" rel="noreferrer">Open in Google Maps</a></section>}
        {session?.role === "admin" && <section className="card wide"><h2>User moderation</h2>{users.map((user) => <div className="listing" key={user.id}><div><strong>{user.email}</strong><span className="muted">{user.role} · {user.active ? "active" : "disabled"}</span></div><button className="secondary" disabled={user.id === session.user_id} onClick={() => toggleUser(user)}>{user.id === session.user_id ? "Current admin" : user.active ? "Disable" : "Enable"}</button></div>)}</section>}
        {session?.role === "admin" && <section className="card wide"><h2>Listing moderation</h2>{adminLots.map((lot) => <div className="listing" key={lot.id}><div><strong>{lot.product}</strong><span className="muted">{lot.quantity_kg} kg · {lot.active ? "active" : "inactive"} · {lot.id}</span></div><button className="secondary" onClick={() => toggleLot(lot)}>{lot.active ? "Deactivate" : "Activate"}</button></div>)}</section>}
        {session?.role === "admin" && <section className="card wide"><h2>All orders</h2>{orders.map((order) => <div className="order-row" key={order.id}><strong>{order.id}</strong><div className="muted">{order.quantity_kg} kg · {order.status} · {order.lot_id}</div></div>)}</section>}
      </div>
    </main>
  </div>;
}
