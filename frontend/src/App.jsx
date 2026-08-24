import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

import {
  FileUp,
  Gavel,
  LayoutDashboard,
  ListChecks,
  ScrollText,
  Users,
} from "lucide-react";


import {
  AuthProvider,
  RequireRole,
} from "./lib/auth";


import Layout from "./components/Layout";


import Landing from "./pages/Landing";


import {
  AdminSignIn,
  SignIn,
  SignUpAdmin,
  SignUpPayer,
  SignUpProvider,
} from "./pages/Auth";


import ProviderDashboard from "./pages/ProviderDashboard";

import NewRequest from "./pages/NewRequest";


import {
  RequestDetail,
  RequestList,
} from "./pages/Requests";


import PayerDashboard from "./pages/PayerDashboard";


import {
  Appeals,
  ReviewCase,
  ReviewQueue,
  Reviewers,
} from "./pages/Review";


import ModelCard from "./pages/ModelCard";


/* =========================================================
   ADMIN / PORTAL PAGES
========================================================= */

import PortalSelection from "./pages/PortalSelection";

import HospitalAdminDashboard
  from "./pages/HospitalAdminDashboard";

import InsuranceAdminDashboard
  from "./pages/InsuranceAdminDashboard";


/* =========================================================
   HOSPITAL / PROVIDER STAFF NAVIGATION
========================================================= */

const PROVIDER_NAV = [

  {
    to: "/hospital",
    label: "Dashboard",
    icon: LayoutDashboard,
    end: true,
  },

  {
    to: "/hospital/new",
    label: "New request",
    icon: FileUp,
  },

  {
    to: "/hospital/requests",
    label: "Requests",
    icon: ListChecks,
  },

  {
    to: "/hospital/models",
    label: "Model card",
    icon: ScrollText,
  },

];


/* =========================================================
   INSURANCE / PAYER STAFF NAVIGATION
========================================================= */

const PAYER_NAV = [

  {
    to: "/payer",
    label: "Dashboard",
    icon: LayoutDashboard,
    end: true,
  },

  {
    to: "/payer/queue",
    label: "Review queue",
    icon: ListChecks,
  },

  {
    to: "/payer/appeals",
    label: "Appeals",
    icon: Gavel,
  },

  {
    to: "/payer/reviewers",
    label: "Reviewers",
    icon: Users,
  },

  {
    to: "/payer/models",
    label: "Model card",
    icon: ScrollText,
  },

];


/* =========================================================
   APP
========================================================= */

export default function App() {

  return (

    <AuthProvider>

      <Router>

        <Routes>


          {/* =================================================
              LANDING
          ================================================= */}

          <Route
            path="/"
            element={<Landing />}
          />


          {/* =================================================
              HOSPITAL PORTAL SELECTION

              LANDING
                  ↓
              HOSPITAL
                  ↓
              CHOOSE ACCESS
                  ↓
              ADMIN / STAFF
          ================================================= */}

          <Route
            path="/hospital/signin"
            element={
              <PortalSelection
                portal="hospital"
              />
            }
          />

          <Route
            path="/hospital/portal"
            element={
              <PortalSelection
                portal="hospital"
              />
            }
          />


          {/* =================================================
              HOSPITAL STAFF SIGN IN
          ================================================= */}

          <Route
            path="/hospital/staff/signin"
            element={
              <SignIn
                portal="provider"
                access="staff"
              />
            }
          />


          {/* =================================================
              HOSPITAL STAFF SIGN UP
          ================================================= */}

          <Route
            path="/hospital/staff/signup"
            element={
              <SignUpProvider />
            }
          />


          {/* =================================================
              HOSPITAL ADMIN SIGN IN
          ================================================= */}

          <Route
            path="/hospital/admin/signin"
            element={
              <AdminSignIn
                portal="provider"
              />
            }
          />


          {/* =================================================
              HOSPITAL ADMIN SIGN UP
          ================================================= */}

          <Route
            path="/hospital/admin/signup"
            element={
              <SignUpAdmin
                portal="provider"
              />
            }
          />


          {/* =================================================
              HOSPITAL STAFF BACKWARD COMPATIBILITY
          ================================================= */}

          <Route
            path="/hospital/signup"
            element={
              <SignUpProvider />
            }
          />


          {/* =================================================
              HOSPITAL STAFF DASHBOARD
          ================================================= */}

          <Route
            path="/hospital"
            element={

              <RequireRole
                role="PROVIDER_STAFF"
              >

                <Layout
                  portal="provider"
                  nav={PROVIDER_NAV}
                />

              </RequireRole>

            }
          >

            <Route
              index
              element={
                <ProviderDashboard />
              }
            />

            <Route
              path="new"
              element={
                <NewRequest />
              }
            />

            <Route
              path="requests"
              element={
                <RequestList />
              }
            />

            <Route
              path="requests/:id"
              element={
                <RequestDetail />
              }
            />

            <Route
              path="models"
              element={
                <ModelCard />
              }
            />

          </Route>


          {/* =================================================
              HOSPITAL ADMIN DASHBOARD
          ================================================= */}

          <Route
            path="/hospital/admin"
            element={

              <RequireRole
                role="PROVIDER_ADMIN"
              >

                <HospitalAdminDashboard />

              </RequireRole>

            }
          />


          {/* =================================================
              INSURANCE PORTAL SELECTION
          ================================================= */}

          <Route
            path="/payer/signin"
            element={
              <PortalSelection
                portal="payer"
              />
            }
          />

          <Route
            path="/payer/portal"
            element={
              <PortalSelection
                portal="payer"
              />
            }
          />


          {/* =================================================
              INSURANCE STAFF SIGN IN
          ================================================= */}

          <Route
            path="/payer/staff/signin"
            element={
              <SignIn
                portal="payer"
                access="staff"
              />
            }
          />


          {/* =================================================
              INSURANCE STAFF SIGN UP
          ================================================= */}

          <Route
            path="/payer/staff/signup"
            element={
              <SignUpPayer />
            }
          />


          {/* =================================================
              INSURANCE ADMIN SIGN IN
          ================================================= */}

          <Route
            path="/payer/admin/signin"
            element={
              <AdminSignIn
                portal="payer"
              />
            }
          />


          {/* =================================================
              INSURANCE ADMIN SIGN UP
          ================================================= */}

          <Route
            path="/payer/admin/signup"
            element={
              <SignUpAdmin
                portal="payer"
              />
            }
          />


          {/* =================================================
              INSURANCE STAFF BACKWARD COMPATIBILITY
          ================================================= */}

          <Route
            path="/payer/signup"
            element={
              <SignUpPayer />
            }
          />


          {/* =================================================
              INSURANCE STAFF DASHBOARD
          ================================================= */}

          <Route
            path="/payer"
            element={

              <RequireRole
                role="PAYER_REVIEWER"
              >

                <Layout
                  portal="payer"
                  nav={PAYER_NAV}
                />

              </RequireRole>

            }
          >

            <Route
              index
              element={
                <PayerDashboard />
              }
            />

            <Route
              path="queue"
              element={
                <ReviewQueue />
              }
            />

            <Route
              path="cases/:id"
              element={
                <ReviewCase />
              }
            />

            <Route
              path="appeals"
              element={
                <Appeals />
              }
            />

            <Route
              path="reviewers"
              element={
                <Reviewers />
              }
            />

            <Route
              path="models"
              element={
                <ModelCard />
              }
            />

          </Route>


          {/* =================================================
              INSURANCE ADMIN DASHBOARD
          ================================================= */}

          <Route
            path="/payer/admin"
            element={

              <RequireRole
                role="PAYER_ADMIN"
              >

                <InsuranceAdminDashboard />

              </RequireRole>

            }
          />


          {/* =================================================
              FALLBACK
          ================================================= */}

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />


        </Routes>

      </Router>

    </AuthProvider>

  );

}