import {
  ArrowLeft,
  ArrowRight,
  Building2,
  ShieldCheck,
  UserCog,
  Users,
} from "lucide-react";

import { Link } from "react-router-dom";


export default function PortalSelection({ portal }) {

  const hospital = portal === "hospital";

  const config = hospital
    ? {
        eyebrow: "Hospital portal",

        title: "Choose your access",

        description:
          "Select whether you are accessing the hospital administration portal or the staff authorization workspace.",

        icon: Building2,

        adminTitle: "Admin Portal",

        adminDescription:
          "Monitor staff activity, submitted cases, audit history and hospital-wide authorization operations.",

        staffTitle: "Staff Portal",

        staffDescription:
          "Create authorization requests, upload documents and manage existing hospital cases.",

        adminTo: "/hospital/admin/signin",

        staffTo: "/hospital/staff/signin",

        accent: "provider",
      }
    : {
        eyebrow: "Insurance portal",

        title: "Choose your access",

        description:
          "Select whether you are accessing the insurance administration portal or the reviewer workspace.",

        icon: ShieldCheck,

        adminTitle: "Admin Portal",

        adminDescription:
          "Monitor reviewer activity, case assignments, decisions and the complete insurance audit history.",

        staffTitle: "Staff Portal",

        staffDescription:
          "Review authorization cases, handle appeals and make adjudication decisions.",

        adminTo: "/payer/admin/signin",

        staffTo: "/payer/staff/signin",

        accent: "payer",
      };


  const PortalIcon = config.icon;

  const provider = config.accent === "provider";


  return (
    <div className="min-h-screen bg-canvas">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="border-b border-rule bg-white/90 backdrop-blur-xl">

        <div className="mx-auto flex h-16 max-w-[1100px] items-center px-6">

          <Link
            to="/"
            className="flex items-center gap-2 text-sm font-medium text-ink-2 hover:text-ink"
          >
            <ArrowLeft size={16} />
            Back
          </Link>

        </div>

      </header>


      {/* =====================================================
          MAIN
      ===================================================== */}

      <main className="mx-auto max-w-[1100px] px-6 py-16">

        <div className="mx-auto max-w-2xl text-center">

          {/* Portal icon */}

          <div
            className={`mx-auto grid h-14 w-14 place-items-center rounded-2xl ${
              provider
                ? "bg-provider text-white"
                : "bg-payer text-white"
            }`}
          >
            <PortalIcon size={26} />
          </div>


          {/* Eyebrow */}

          <div className="eyebrow mt-6">
            {config.eyebrow}
          </div>


          {/* Heading */}

          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            {config.title}
          </h1>


          {/* Description */}

          <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-ink-2">
            {config.description}
          </p>

        </div>


        {/* =================================================
            PORTAL CARDS
        ================================================= */}

        <div className="mt-12 grid gap-5 md:grid-cols-2">

          {/* ADMIN */}

          <PortalOption
            icon={UserCog}
            title={config.adminTitle}
            description={config.adminDescription}
            to={config.adminTo}
            accent={config.accent}
            admin
          />


          {/* STAFF */}

          <PortalOption
            icon={Users}
            title={config.staffTitle}
            description={config.staffDescription}
            to={config.staffTo}
            accent={config.accent}
          />

        </div>

      </main>

    </div>
  );
}


/* =========================================================
   PORTAL OPTION
========================================================= */

function PortalOption({
  icon: Icon,
  title,
  description,
  to,
  accent,
  admin = false,
}) {

  const provider = accent === "provider";


  return (
    <Link
      to={to}
      className="group relative overflow-hidden rounded-2xl border border-rule bg-white p-7 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-elevated"
    >

      {/* Background decoration */}

      <div
        className={`absolute right-0 top-0 h-40 w-40 rounded-full blur-3xl ${
          provider
            ? "bg-blue-100/60"
            : "bg-violet-100/60"
        }`}
      />


      <div className="relative">

        {/* Icon + badge */}

        <div className="flex items-start justify-between">

          <div
            className={`grid h-12 w-12 place-items-center rounded-xl ${
              provider
                ? "bg-provider text-white"
                : "bg-payer text-white"
            }`}
          >
            <Icon size={22} />
          </div>


          {admin && (
            <span
              className={`chip ${
                provider
                  ? "border-provider-line bg-provider-soft text-provider"
                  : "border-payer-line bg-payer-soft text-payer"
              }`}
            >
              Administration
            </span>
          )}

        </div>


        {/* Title */}

        <h2 className="mt-7 text-xl font-bold tracking-tight">
          {title}
        </h2>


        {/* Description */}

        <p className="mt-3 text-sm leading-6 text-ink-2">
          {description}
        </p>


        {/* Continue */}

        <div className="mt-7 inline-flex items-center gap-2 text-sm font-semibold">

          <span
            className={
              provider
                ? "text-provider"
                : "text-payer"
            }
          >
            Continue
          </span>

          <ArrowRight
            size={15}
            className="transition-transform group-hover:translate-x-1"
          />

        </div>

      </div>

    </Link>
  );
}