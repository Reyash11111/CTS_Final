import {
  ArrowRight,
  Building2,
  BrainCircuit,
  CheckCircle2,
  Clock,
  FileCheck2,
  Linkedin,
  Lock,
  Mail,
  MapPin,
  MessageSquareText,
  Phone,
  ShieldCheck,
  Twitter,
  UserCheck,
  Workflow,
} from "lucide-react";
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="min-h-screen bg-canvas">
      <SiteHeader />

      <main>
        <Hero />
        <PortalSection />
        <WorkflowSection />
        <TrustSection />
        <MetricsSection />
      </main>

      <SiteFooter />
    </div>
  );
}

/* ============================================================
   HEADER
============================================================ */

function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-rule bg-white/90 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between px-6 lg:px-10">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-provider text-white">
            <ShieldCheck size={19} />
          </div>

          <div>
            <div className="text-sm font-bold tracking-tight text-ink">
              PriorAuth AI
            </div>
            <div className="text-[10px] font-medium uppercase tracking-[.14em] text-ink-3">
              Authorization intelligence
            </div>
          </div>
        </div>

        <nav className="hidden items-center gap-8 md:flex">
          <a href="#workflow" className="text-[13px] font-medium text-ink-2 hover:text-ink">
            How it works
          </a>
          <a href="#trust" className="text-[13px] font-medium text-ink-2 hover:text-ink">
            Security &amp; compliance
          </a>
          <a href="#contact" className="text-[13px] font-medium text-ink-2 hover:text-ink">
            Contact
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-1.5 chip border-approve-line bg-approve-soft text-approve sm:inline-flex">
            <span className="status-dot bg-approve" />
            Platform operational
          </span>

          <Link to="/hospital/portal" className="btn border-rule bg-white text-ink hover:bg-canvas">
            Sign in
          </Link>
        </div>
      </div>
    </header>
  );
}

/* ============================================================
   HERO
============================================================ */

function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-rule">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_-10%,rgba(37,99,235,.08),transparent_55%)]" />

      <div className="mx-auto max-w-[820px] px-6 py-20 text-center lg:py-28 lg:px-10">
        <div className="inline-flex items-center gap-2 rounded-full border border-provider-line bg-provider-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[.12em] text-provider">
          Built for hospital and payer teams
        </div>

        <h1 className="mx-auto mt-6 max-w-[720px] text-[2.75rem] font-bold leading-[1.08] tracking-[-.03em] text-ink sm:text-6xl">
          Prior authorization,
          <br />
          decided in minutes.
        </h1>

        <p className="mx-auto mt-6 max-w-xl text-[15px] leading-7 text-ink-2">
          Submit a request, see exactly where it stands, and get a clear
          answer — without days of phone calls and faxed paperwork.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link to="/hospital/signup" className="btn border-provider bg-provider text-white hover:bg-provider-deep">
            Request a demo
            <ArrowRight size={15} />
          </Link>
          <a href="#workflow" className="text-sm font-semibold text-ink-2 hover:text-ink">
            See how it works
          </a>
        </div>

        <dl className="mx-auto mt-14 grid max-w-lg grid-cols-3 gap-6 border-t border-rule pt-8">
          <div>
            <dt className="text-2xs font-medium uppercase tracking-wide text-ink-3">
              Requests handled
            </dt>
            <dd className="num mt-1 text-2xl font-bold text-ink">1.2M+</dd>
          </div>
          <div>
            <dt className="text-2xs font-medium uppercase tracking-wide text-ink-3">
              Faster answers
            </dt>
            <dd className="num mt-1 text-2xl font-bold text-ink">40%</dd>
          </div>
          <div>
            <dt className="text-2xs font-medium uppercase tracking-wide text-ink-3">
              Organizations
            </dt>
            <dd className="num mt-1 text-2xl font-bold text-ink">310+</dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

/* ============================================================
   PORTAL CARDS
============================================================ */

function PortalSection() {
  return (
    <section className="border-b border-rule bg-white">
      <div className="mx-auto max-w-[1280px] px-6 py-16 lg:px-10 lg:py-20">
        <div className="max-w-2xl">
          <div className="eyebrow">Two portals, one workflow</div>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Choose your side of the desk
          </h2>
        </div>

        <div className="mt-10 grid gap-5 lg:grid-cols-2">
          <PortalCard
            to="/hospital/portal"
            signupTo="/hospital/signup"
            icon={Building2}
            eyebrow="Hospital portal"
            title="Submit a request"
            description="Upload your paperwork once — we'll pull out the patient and treatment details for you, so your staff doesn't have to re-type anything."
            accent="provider"
            points={[
              { icon: FileCheck2, text: "Upload paperwork, skip the manual data entry" },
              { icon: Clock, text: "Track every request in real time, no phone calls" },
              { icon: CheckCircle2, text: "Simple approvals get an answer right away" },
              { icon: MessageSquareText, text: "See the reason behind every decision" },
            ]}
          />

          <PortalCard
            to="/payer/portal"
            signupTo="/payer/signup"
            icon={ShieldCheck}
            eyebrow="Payer portal"
            title="Review requests"
            description="See what needs your attention first, understand why, and get every case to the right reviewer without digging through paperwork."
            accent="payer"
            points={[
              { icon: Clock, text: "Urgent cases automatically rise to the top" },
              { icon: MessageSquareText, text: "Plain-language reason behind every flag" },
              { icon: UserCheck, text: "Cases go straight to the right specialist" },
              { icon: FileCheck2, text: "Full history for every case, one click away" },
            ]}
          />
        </div>
      </div>
    </section>
  );
}

function PortalCard({ to, signupTo, icon: Icon, eyebrow, title, description, accent, points }) {
  const provider = accent === "provider";

  const styles = provider
    ? {
        icon: "bg-provider text-white",
        badge: "border-provider-line bg-provider-soft text-provider",
        button: "border-provider bg-provider text-white hover:bg-provider-deep",
        bar: "bg-provider",
      }
    : {
        icon: "bg-payer text-white",
        badge: "border-payer-line bg-payer-soft text-payer",
        button: "border-payer bg-payer text-white hover:bg-payer-deep",
        bar: "bg-payer",
      };

  return (
    <section className="group relative overflow-hidden rounded-2xl border border-rule bg-white shadow-card transition-shadow duration-200 hover:shadow-elevated">
      <div className={`h-1 w-full ${styles.bar}`} />

      <div className="p-6 lg:p-8">
        <div className="flex items-start justify-between">
          <div className={`grid h-11 w-11 place-items-center rounded-xl ${styles.icon}`}>
            <Icon size={21} />
          </div>

          <span className={`chip ${styles.badge}`}>{eyebrow}</span>
        </div>

        <h3 className="mt-6 text-xl font-bold tracking-tight text-ink">{title}</h3>

        <p className="mt-2.5 max-w-md text-[13px] leading-6 text-ink-2">{description}</p>

        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {points.map((point) => (
            <li
              key={point.text}
              className="flex items-start gap-2.5 rounded-lg bg-canvas px-3 py-2.5 text-[13px] leading-5 text-ink-2"
            >
              <point.icon
                size={15}
                className={`mt-0.5 shrink-0 ${provider ? "text-provider" : "text-payer"}`}
              />
              {point.text}
            </li>
          ))}
        </ul>

        <div className="mt-8 flex flex-wrap items-center gap-4 border-t border-rule pt-6">
          <Link to={to} className={`btn ${styles.button}`}>
            Enter portal
            <ArrowRight size={15} />
          </Link>

          <Link to={signupTo} className="text-sm font-semibold text-ink-2 hover:text-ink">
            Create account
          </Link>
        </div>
      </div>
    </section>
  );
}

/* ============================================================
   WORKFLOW
============================================================ */

function WorkflowSection() {
  const steps = [
    {
      icon: FileCheck2,
      title: "01 — Extract",
      text: "Structured fields — patient, diagnosis, requested treatment, coding — are pulled from the submitted packet in seconds.",
    },
    {
      icon: BrainCircuit,
      title: "02 — Evaluate",
      text: "The request is checked against medical-necessity criteria and scored for urgency and appeal risk, with the reasoning shown alongside.",
    },
    {
      icon: Workflow,
      title: "03 — Route & decide",
      text: "Straightforward cases resolve automatically. Complex ones are routed to the reviewer with the right specialty.",
    },
  ];

  return (
    <section id="workflow" className="border-b border-rule">
      <div className="mx-auto max-w-[1280px] px-6 py-16 lg:px-10 lg:py-20">
        <div className="max-w-2xl">
          <div className="eyebrow">How it works</div>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            From packet to decision, in one pass
          </h2>
        </div>

        <div className="relative mt-12 grid gap-8 md:grid-cols-3">
          <div className="absolute left-0 right-0 top-6 hidden h-px bg-rule md:block" />

          {steps.map((step) => (
            <div key={step.title} className="relative">
              <div className="relative z-10 grid h-12 w-12 place-items-center rounded-xl border border-rule bg-white text-provider shadow-card">
                <step.icon size={20} />
              </div>

              <h3 className="mt-5 text-sm font-bold uppercase tracking-wide text-ink-3">
                {step.title}
              </h3>

              <p className="mt-2 text-[13px] leading-6 text-ink-2">{step.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================
   TRUST / COMPLIANCE
============================================================ */

function TrustSection() {
  const badges = [
    { label: "HIPAA compliant" },
    { label: "SOC 2 Type II" },
    { label: "256-bit encryption" },
    { label: "99.95% uptime SLA" },
  ];

  return (
    <section id="trust" className="border-b border-rule bg-white">
      <div className="mx-auto max-w-[1280px] px-6 py-14 lg:px-10">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-canvas text-ink-2">
              <Lock size={17} />
            </div>
            <div>
              <div className="text-sm font-bold text-ink">
                Built to hospital and payer security standards
              </div>
              <div className="text-[13px] text-ink-2">
                Every case is encrypted in transit and at rest, with a full audit trail.
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2.5">
            {badges.map((badge) => (
              <span
                key={badge.label}
                className="chip border-rule bg-canvas text-ink-2"
              >
                {badge.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ============================================================
   METRICS
============================================================ */

function MetricsSection() {
  const metrics = [
    { value: "1.2M+", label: "Authorizations processed annually" },
    { value: "40%", label: "Faster time-to-decision" },
    { value: "98.4%", label: "Field extraction accuracy" },
    { value: "310+", label: "Hospital and payer organizations" },
  ];

  return (
    <section>
      <div className="mx-auto max-w-[1280px] px-6 py-16 lg:px-10 lg:py-20">
        <div className="grid gap-8 rounded-2xl border border-rule bg-white p-8 shadow-card sm:grid-cols-2 lg:grid-cols-4 lg:p-10">
          {metrics.map((metric) => (
            <div key={metric.label}>
              <div className="num text-3xl font-bold tracking-tight text-ink">
                {metric.value}
              </div>
              <div className="mt-1.5 text-[13px] text-ink-2">{metric.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============================================================
   FOOTER
============================================================ */

function SiteFooter() {
  return (
    <footer id="contact" className="border-t border-rule bg-white">
      <div className="mx-auto max-w-[1280px] px-6 py-14 lg:px-10">
        <div className="grid gap-10 lg:grid-cols-[1.3fr_1fr_1fr_1.2fr]">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-provider text-white">
                <ShieldCheck size={19} />
              </div>
              <div className="text-sm font-bold tracking-tight text-ink">
                PriorAuth AI
              </div>
            </div>

            <p className="mt-4 max-w-xs text-[13px] leading-6 text-ink-2">
              Authorization intelligence for hospital and payer teams —
              built to make medical-necessity decisions faster and easier
              to explain.
            </p>

            <div className="mt-5 flex items-center gap-3">
              <a
                href="https://linkedin.com"
                aria-label="LinkedIn"
                className="grid h-8 w-8 place-items-center rounded-lg border border-rule text-ink-3 hover:text-ink"
              >
                <Linkedin size={15} />
              </a>
              <a
                href="https://twitter.com"
                aria-label="Twitter"
                className="grid h-8 w-8 place-items-center rounded-lg border border-rule text-ink-3 hover:text-ink"
              >
                <Twitter size={15} />
              </a>
            </div>
          </div>

          <div>
            <div className="text-2xs font-semibold uppercase tracking-wide text-ink-3">
              Product
            </div>
            <ul className="mt-4 space-y-2.5 text-[13px] text-ink-2">
              <li><a href="#workflow" className="hover:text-ink">How it works</a></li>
              <li><Link to="/hospital/portal" className="hover:text-ink">Hospital portal</Link></li>
              <li><Link to="/payer/portal" className="hover:text-ink">Payer portal</Link></li>
              <li><a href="#trust" className="hover:text-ink">Security</a></li>
            </ul>
          </div>

          <div>
            <div className="text-2xs font-semibold uppercase tracking-wide text-ink-3">
              Company
            </div>
            <ul className="mt-4 space-y-2.5 text-[13px] text-ink-2">
              <li><a href="#" className="hover:text-ink">About</a></li>
              <li><a href="#" className="hover:text-ink">Careers</a></li>
              <li><a href="#" className="hover:text-ink">Press</a></li>
              <li><a href="#" className="hover:text-ink">Privacy policy</a></li>
            </ul>
          </div>

          <div>
            <div className="text-2xs font-semibold uppercase tracking-wide text-ink-3">
              Contact
            </div>
            <ul className="mt-4 space-y-3 text-[13px] text-ink-2">
              <li className="flex items-start gap-2.5">
                <MapPin size={15} className="mt-0.5 shrink-0 text-ink-3" />
                548 Market Street, Suite 91000
                <br />
                San Francisco, CA 94104
              </li>
              <li className="flex items-center gap-2.5">
                <Phone size={15} className="shrink-0 text-ink-3" />
                <a href="tel:+18005550142" className="hover:text-ink">
                  +1 (800) 555-0142
                </a>
              </li>
              <li className="flex items-center gap-2.5">
                <Mail size={15} className="shrink-0 text-ink-3" />
                <a href="mailto:hello@priorauth.ai" className="hover:text-ink">
                  hello@priorauth.ai
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-rule pt-6 text-2xs text-ink-3 sm:flex-row">
          <span>© 2026 PriorAuth AI, Inc. All rights reserved.</span>
          <span>HIPAA compliant · SOC 2 Type II certified</span>
        </div>
      </div>
    </footer>
  );
}