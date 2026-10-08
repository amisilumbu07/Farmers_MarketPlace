import Link from "next/link";

const ROLES = [
  ["buyer", "Buyer", "Post demand, order produce, confirm delivery."],
  ["farmer", "Farmer", "Accept orders and manage your farm."],
  ["transporter", "Transporter", "Confirm pooled transport trips."],
  ["admin", "Admin", "Moderate users, listings and disputes."],
];

// ponytail: demo-only sign-in. Each role opens the test console with sample data; real email login (existing /login and /register API) comes with the role routes.
export default async function Login({ searchParams }: { searchParams: Promise<{ role?: string }> }) {
  const { role: chosen } = await searchParams;
  return <div className="shell">
    <header className="topbar">
      <div className="topbar-row">
        <Link className="logo" href="/" aria-label="AgriLink home"><span>AgriLink</span></Link>
      </div>
    </header>
    <main className="content narrow">
      <h1>Sign in</h1>
      <p className="muted">Choose a role to try the marketplace with sample data. Nothing here is real money.</p>
      <div className="role-list">{ROLES.map(([role, title, text]) => <Link className={`card role-card${chosen === role ? " chosen" : ""}`} href={`/tests?role=${role}`} key={role}><h3>{title}</h3><p className="muted">{text}</p><span className="pill">Sign in as {title.toLowerCase()}</span></Link>)}</div>
      <p className="muted foot"><Link href="/">Back to home</Link></p>
    </main>
  </div>;
}
