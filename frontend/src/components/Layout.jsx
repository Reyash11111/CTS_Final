import { useEffect, useState } from "react";
import Chatbot from "./Chatbot";

import {
  Bell,
  ChevronDown,
  CircleDot,
  LogOut,
  Menu,
  PauseCircle,
  ShieldCheck,
  X,
  ListChecks,
  AlertTriangle,
} from "lucide-react";

import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";

import { api } from "../lib/api";
import { useAuth } from "../lib/auth";


export default function Layout({ portal, nav }) {
  const { user, logout, refresh } = useAuth();
  const navigate = useNavigate();

  const [busy, setBusy] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isPayer = portal === "payer";

  const mark = isPayer
    ? "bg-payer"
    : "bg-provider";


  /* =====================================================
     REFRESH USER
     ===================================================== */

  useEffect(() => {
    refresh().catch(() => {});
  }, []);


  /* =====================================================
     REVIEWER AVAILABILITY
     ===================================================== */

  const toggleAvailability = async () => {
    if (!user) return;

    setBusy(true);

    try {
      await api.patch(
        "/api/auth/availability",
        {
          is_available: !user.is_available,

          unavailable_reason: user.is_available
            ? "On another case"
            : null,
        }
      );

      await refresh();

    } finally {
      setBusy(false);
    }
  };


  /* =====================================================
     LOGOUT
     ===================================================== */

  const handleLogout = () => {
    logout();
    navigate("/");
  };


  return (
    <div className="min-h-screen bg-canvas">

      {/* =================================================
          HEADER
         ================================================= */}

      <header className="sticky top-0 z-40 border-b border-rule bg-white/90 backdrop-blur-xl">

        <div className="flex h-16 items-center justify-between px-4 lg:px-6">

          {/* LEFT SIDE */}
          <div className="flex items-center gap-3">

            {/* MOBILE MENU */}
            <button
              className="grid h-10 w-10 place-items-center rounded-lg border border-rule bg-white text-ink-2 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={18} />
            </button>


            {/* LOGO */}
            <div className="flex items-center gap-3">

              <div
                className={`grid h-10 w-10 place-items-center rounded-xl text-white shadow-lg ${
                  isPayer
                    ? "bg-payer shadow-payer/20"
                    : "bg-provider shadow-provider/20"
                }`}
              >
                <ShieldCheck size={20} />
              </div>


              <div className="hidden sm:block">

                <div className="text-sm font-bold tracking-tight">
                  PriorAuth AI
                </div>

                <div className="text-[10px] font-medium uppercase tracking-[.12em] text-ink-3">

                  {isPayer
                    ? "Payer intelligence"
                    : "Hospital management"}

                </div>

              </div>

            </div>

          </div>


          {/* =================================================
              HEADER RIGHT
             ================================================= */}

          <div className="flex items-center gap-2">


            {/* REVIEWER AVAILABILITY */}

            {isPayer && user && (

              <button
                onClick={toggleAvailability}
                disabled={busy}
                className={`hidden items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition sm:flex ${
                  user.is_available
                    ? "border-approve-line bg-approve-soft text-approve"
                    : "border-rule bg-slate-50 text-ink-2"
                }`}
              >

                {user.is_available ? (
                  <CircleDot size={14} />
                ) : (
                  <PauseCircle size={14} />
                )}

                {user.is_available
                  ? "Available"
                  : "Unavailable"}

              </button>

            )}


            {/* NOTIFICATIONS */}

            <button
              className="grid h-10 w-10 place-items-center rounded-lg border border-rule bg-white text-ink-2 hover:bg-slate-50"
              title="Notifications"
            >
              <Bell size={17} />
            </button>


            {/* USER */}

            {user && (

              <div className="hidden items-center gap-2 pl-2 sm:flex">

                <div
                  className={`grid h-9 w-9 place-items-center rounded-full text-xs font-bold text-white ${mark}`}
                >
                  {user.full_name
                    ?.charAt(0)
                    ?.toUpperCase() || "U"}
                </div>


                <div className="max-w-[150px]">

                  <div className="truncate text-xs font-semibold">
                    {user.full_name}
                  </div>

                  <div className="truncate text-[10px] text-ink-3">
                    {user.organization_name}
                  </div>

                </div>


                <ChevronDown
                  size={14}
                  className="text-ink-3"
                />

              </div>

            )}


            {/* LOGOUT */}

            <button
              onClick={handleLogout}
              className="grid h-10 w-10 place-items-center rounded-lg border border-rule bg-white text-ink-3 hover:bg-red-50 hover:text-deny"
              title="Sign out"
            >
              <LogOut size={16} />
            </button>

          </div>

        </div>

      </header>


      {/* =====================================================
          MAIN BODY
         ===================================================== */}

      <div className="flex">


        {/* =================================================
            DESKTOP SIDEBAR
           ================================================= */}

        <aside className="sidebar-gradient sticky top-16 hidden h-[calc(100vh-64px)] w-64 shrink-0 border-r border-rule lg:block">

          <Sidebar
            nav={nav}
            portal={portal}
            user={user}
          />

        </aside>


        {/* =================================================
            MOBILE SIDEBAR
           ================================================= */}

        {mobileOpen && (

          <div className="fixed inset-0 z-50 lg:hidden">

            {/* OVERLAY */}

            <div
              className="absolute inset-0 bg-slate-950/30 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />


            {/* SIDEBAR */}

            <aside className="relative h-full w-80 bg-white shadow-elevated">

              <div className="flex h-16 items-center justify-between border-b border-rule px-5">

                <div className="font-bold">
                  Navigation
                </div>


                <button
                  onClick={() => setMobileOpen(false)}
                  className="grid h-9 w-9 place-items-center rounded-lg border border-rule"
                  aria-label="Close navigation"
                >
                  <X size={17} />
                </button>

              </div>


              <Sidebar
                nav={nav}
                portal={portal}
                user={user}
                onNavigate={() => setMobileOpen(false)}
              />

            </aside>

          </div>

        )}


        {/* =================================================
            PAGE CONTENT
           ================================================= */}

        <main className="min-w-0 flex-1">

          <div className="mx-auto max-w-[1500px] px-4 py-6 lg:px-8 lg:py-8">

            <div className="page-enter">

              <Outlet />

            </div>


            {/* CHATBOT */}

            <Chatbot portal={portal} />

          </div>

        </main>

      </div>

    </div>
  );
}


/* =========================================================
   SIDEBAR
   ========================================================= */

function Sidebar({
  nav,
  portal,
  user,
  onNavigate,
}) {

  const isPayer = portal === "payer";


  return (

    <div className="flex h-full flex-col px-3 py-5">


      {/* =================================================
          WORKSPACE
         ================================================= */}

      <div className="mb-5 rounded-xl bg-slate-50 p-4">

        <div className="text-[10px] font-semibold uppercase tracking-[.13em] text-ink-3">
          Workspace
        </div>


        <div className="mt-2 text-sm font-bold">

          {isPayer
            ? "Payer operations"
            : "Hospital operations"}

        </div>


        <div className="mt-1 text-xs text-ink-3">

          {user?.organization_name ||
            "Organization"}

        </div>

      </div>


      {/* =================================================
          NAVIGATION
         ================================================= */}

      <nav className="space-y-1">

        {nav.map((item) => {

          const Icon = item.icon;

          /*
           * Detect the Human Review Queue.
           *
           * This allows us to give the queue a special
           * visual treatment without changing routing.
           */

          const isReviewQueue =
            isPayer &&
            (
              item.to === "/payer/queue" ||
              item.label?.toLowerCase().includes("review queue")
            );


          return (

            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onNavigate}

              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-semibold transition ${
                  isActive
                    ? isPayer
                      ? "bg-payer-soft text-payer"
                      : "bg-provider-soft text-provider"
                    : "text-ink-2 hover:bg-slate-100 hover:text-ink"
                }`
              }
            >

              {/* ICON */}

              <Icon
                size={17}
                strokeWidth={1.9}
              />


              {/* LABEL */}

              <span className="flex-1">

                {isReviewQueue
                  ? "Human Review Queue"
                  : item.label}

              </span>


              {/* =================================================
                  HUMAN REVIEW INDICATOR
                 ================================================= */}

              {isReviewQueue && (

                <span
                  className="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-amber-700"
                  title="Cases requiring human review"
                >
                  <AlertTriangle size={10} />

                  Review

                </span>

              )}

            </NavLink>

          );

        })}

      </nav>


      {/* =================================================
          HUMAN REVIEW INFORMATION
         ================================================= */}

      {isPayer && (

        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50/70 p-4">

          <div className="flex items-center gap-2">

            <div className="grid h-7 w-7 place-items-center rounded-lg bg-amber-100 text-amber-700">

              <ListChecks size={15} />

            </div>


            <div>

              <div className="text-xs font-bold text-amber-900">
                Human Review
              </div>

              <div className="text-[10px] text-amber-700">
                Priority-based cases
              </div>

            </div>

          </div>


          <p className="mt-3 text-[10px] leading-4 text-amber-800">

            AI-flagged requests requiring human
            verification are organized in the
            review queue based on clinical severity.

          </p>

        </div>

      )}


      {/* =================================================
          HELP
         ================================================= */}

      <div className="mt-auto rounded-xl border border-rule bg-white p-4">

        <div className="flex items-center gap-2">

          <div
            className={`h-2 w-2 rounded-full ${
              isPayer
                ? "bg-payer"
                : "bg-provider"
            }`}
          />

          <span className="text-xs font-semibold">
            Need help?
          </span>

        </div>


        <p className="mt-2 text-[10px] leading-4 text-ink-3">

          Upload your documents and we'll help
          you complete the request.

        </p>

      </div>

    </div>

  );
}