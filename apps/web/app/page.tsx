import Link from "next/link";
import type { ReactNode } from "react";

const icon = (children: ReactNode) => <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>;
const ICONS = {
  leaf: icon(<><path d="M5 19c0-8 5-13 14-14 0 9-5 14-14 14z" /><path d="M5 19c3-4 6-7 10-9" /></>),
  truck: icon(<><path d="M2 6h11v10H2zM13 10h4l3 3v3h-7" /><circle cx="7" cy="17.5" r="1.8" /><circle cx="16.5" cy="17.5" r="1.8" /></>),
  shield: icon(<><path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z" /><path d="M9 12l2 2 4-4" /></>),
  globe: icon(<><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" /></>),
};

const BENEFITS = [
  ["leaf", "green", "Better income for farmers"],
  ["truck", "orange", "Lower transport costs"],
  ["shield", "blue", "Trusted and verified supply"],
  ["globe", "purple", "Fresh, quality food at scale"],
] as const;

const TILES = [
  ["farmer", "Farmers", "green", "/img/role-farmers.jpg", "50% 20%", "Farmer harvesting vegetables in a field", "See incoming orders, accept them and keep your farm up to date."],
  ["transporter", "Transporters", "orange", "/img/role-transporters.jpg", "50% 50%", "Truck loaded with crates of fresh produce", "Find pooled loads on your route and confirm a trip."],
  ["buyer", "Buyers", "blue", "/img/role-buyers.jpg", "50% 8%", "Chef plating a fresh salad", "Restaurants, hotels and retailers: post demand and follow delivery."],
] as const;

const FEATURES = [
  ["Fresh from the farm", "Farmers list what they have and when it is ready. Buyers see real stock, price per kilo and distance."],
  ["Matched for you", "Post what you need. The marketplace combines nearby farms into one order, ranked by distance, price and reliability."],
  ["Shared transport", "Compatible orders ride on one truck, so each trip costs less. Transporters see pooled routes and confirm a quote."],
  ["A record you can trust", "Each pickup and delivery is signed and kept in order, and disputes are resolved with that evidence. The record is anchored on Solana."],
];

const Mark = () => <svg viewBox="0 0 40 40" width="36" height="36" aria-hidden="true"><path d="M6 22c0-9 6-15 15-15 0 9-6 16-15 15z" fill="#2e9e5b" /><path d="M13 35c-1-9 4-16 13-17 1 9-4 16-13 17z" fill="#19764a" /><path d="M23 5c6 0 11 4 11 10-6 0-11-4-11-10z" fill="#f08a24" /></svg>;

export default function Landing() {
  return <div className="shell">
    <header className="topbar">
      <div className="topbar-row wrap">
        <Link className="logo" href="/" aria-label="AgriLink home"><Mark /><span>Agri<span className="accent">Link</span></span></Link>
        <div className="topbar-actions"><span className="built-on">Built on Solana</span><Link className="button" href="/login">Sign in</Link></div>
      </div>
    </header>
    <main>
      <section className="hero2">
        <div className="hills" aria-hidden="true"><svg viewBox="0 0 1440 220" preserveAspectRatio="none"><path d="M0 120 C180 60 320 150 520 100 C720 50 860 140 1060 90 C1220 50 1340 90 1440 70 V220 H0z" fill="#cfe5c4" opacity=".7" /><path d="M0 170 C220 120 380 200 620 150 C860 100 1040 190 1240 140 C1330 118 1400 140 1440 130 V220 H0z" fill="#a9d29a" opacity=".75" /></svg></div>
        <div className="wrap hero2-grid">
          <div className="hero2-text">
            <p className="tagline">Real Farmers · Real Food · Trusted Supply · A More Resilient Future</p>
            <h1>From Local Farms <br />to <span className="accent">Global Tables</span></h1>
            <p className="lead">Connecting farmers, transporters and professional buyers through a transparent, efficient and trusted marketplace.</p>
            <ul className="benefits">{BENEFITS.map(([name, tone, label]) => <li key={name}><span className={`benefit-icon ${tone}`}>{ICONS[name]}</span>{label}</li>)}</ul>
            <Link className="button cta" href="/login"><span>One Reliable Supplier<br />From Many Small Farms</span><span aria-hidden="true">→</span></Link>
            <p className="demo-link"><Link href="/tests?role=buyer">Or browse the demo market</Link></p>
          </div>
          <div className="hero2-photo"><img src="/img/hero-farmer.jpg" width="230" height="641" alt="Smiling farmer holding a crate of tomatoes and lettuce" fetchPriority="high" /></div>
          <ol className="journey" aria-label="How the marketplace connects people">{TILES.map(([role, title, tone, src, pos, alt]) => <li key={role}>
            <Link href={`/login?role=${role}`}><img src={src} alt={alt} width="72" height="72" style={{ objectPosition: pos }} /><span className={`chip-inline ${tone}`}>{title}</span></Link>
          </li>)}</ol>
        </div>
      </section>
      <div className="claims"><span>Many Small Farms<br />One Large Supply</span><span>Lower Costs<br />Higher Income</span><span>Transparent<br />On-Chain Records</span></div>
      <section className="content">
        <h2 className="section-title">Sign in as</h2>
        <div className="tiles">{TILES.map(([role, title, tone, src, pos, alt, text]) => <Link className="tile" href={`/login?role=${role}`} key={role}>
          <img src={src} alt={alt} loading="lazy" style={{ objectPosition: pos }} /><span className={`chip ${tone}`}>{title}</span>
          <div className="tile-body"><p>{text}</p><span className="pill">Continue</span></div>
        </Link>)}</div>
        <p className="muted admin-link">Running the marketplace? <Link href="/login?role=admin">Sign in as admin</Link></p>
        <h2 className="section-title">What it does</h2>
        <div className="feature-grid">{FEATURES.map(([title, text]) => <article className="card" key={title}><h3>{title}</h3><p className="muted">{text}</p></article>)}</div>
        <p className="muted foot">Demo mode: sign-in uses sample data. <Link href="/tests">Open the full test console</Link>.</p>
      </section>
    </main>
  </div>;
}
