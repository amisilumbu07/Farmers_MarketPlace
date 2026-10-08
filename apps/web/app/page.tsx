import Link from "next/link";

const FEATURES = [
  ["Fresh from the farm", "Farmers list what they have and when it is ready. Buyers see real stock, price per kilo and distance."],
  ["Matched for you", "Post what you need. The marketplace combines nearby farms into one order, ranked by distance, price and reliability."],
  ["Shared transport", "Compatible orders ride on one truck, so each trip costs less. Transporters see pooled routes and confirm a quote."],
  ["A record you can trust", "Each pickup and delivery is signed and kept in order, and disputes are resolved with that evidence. The record is anchored on Solana."],
];

const ROLES = [
  ["buyer", "Buyer", "Restaurants, shops and institutions: post demand, get matched, follow delivery."],
  ["farmer", "Farmer", "See incoming orders, accept them and keep your farm location up to date."],
  ["transporter", "Transporter", "Find pooled loads on your route and confirm a trip."],
  ["admin", "Admin", "Moderate users and listings, and resolve disputes."],
];

export default function Landing() {
  return <div className="shell">
    <header className="topbar">
      <div className="topbar-row">
        <Link className="logo" href="/" aria-label="AgriLink home"><svg viewBox="0 0 40 40" width="32" height="32" aria-hidden="true"><circle cx="20" cy="20" r="18" fill="#19764a" opacity=".12" /><path d="M20 10l4 5h-2v7h-4v-7h-2z" fill="#19764a" /></svg><span>AgriLink</span></Link>
        <Link className="button" href="/login">Sign in</Link>
      </div>
    </header>
    <main>
      <section className="hero">
        <p className="pill">Farm to buyer, with shared transport</p>
        <h1>Fresh produce from local farmers, delivered together.</h1>
        <p className="lead">AgriLink joins many small farms into one reliable supplier. Buyers get steady quantities, farmers reach customers they could not reach alone, and trucks travel fuller.</p>
        <div className="actions hero-actions">
          <Link className="button" href="/login">Sign in</Link>
          <Link className="button secondary" href="/tests?role=buyer">Browse the demo market</Link>
        </div>
      </section>
      <section className="content">
        <h2 className="section-title">What it does</h2>
        <div className="feature-grid">{FEATURES.map(([title, text]) => <article className="card" key={title}><h3>{title}</h3><p className="muted">{text}</p></article>)}</div>
        <h2 className="section-title">Sign in as</h2>
        <div className="feature-grid">{ROLES.map(([role, title, text]) => <Link className="card role-card" href={`/login?role=${role}`} key={role}><h3>{title}</h3><p className="muted">{text}</p><span className="pill">Continue</span></Link>)}</div>
        <p className="muted foot">Demo mode: sign-in uses sample data. <Link href="/tests">Open the full test console</Link>.</p>
      </section>
    </main>
  </div>;
}
