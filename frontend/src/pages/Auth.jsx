import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Alert, Field } from "../components/ui";


/* =========================================================
   THEME
========================================================= */

const THEME = {
  provider: {
    name: "Hospital management",
    home: "/hospital",

    cta:
      "bg-provider text-white border-provider hover:bg-provider-deep",

    link: "text-provider",

    badge:
      "bg-provider-soft text-provider border-provider-line",
  },

  payer: {
    name: "Insurance organization",
    home: "/payer",

    cta:
      "bg-payer text-white border-payer hover:bg-payer-deep",

    link: "text-payer",

    badge:
      "bg-payer-soft text-payer border-payer-line",
  },
};


/* =========================================================
   SHELL
========================================================= */

function Shell({
  portal,
  title,
  subtitle,
  children,
  footer,
}) {
  const t = THEME[portal];

  return (
    <div className="grid min-h-screen place-items-center px-5 py-12">

      <div className="w-full max-w-[420px]">

        <Link
          to="/"
          className="mb-6 inline-flex items-center gap-1.5 text-[13px] text-ink-3 hover:text-ink"
        >
          <ArrowLeft size={13} />
          Choose a different portal
        </Link>


        <div className="card p-7">

          <div className={`chip ${t.badge}`}>
            {t.name}
          </div>


          <h1 className="mt-4 text-2xl font-semibold">
            {title}
          </h1>


          <p className="mt-1.5 text-[13px] text-ink-2">
            {subtitle}
          </p>


          <div className="mt-6 space-y-4">
            {children}
          </div>

        </div>


        <p className="mt-5 text-center text-[13px] text-ink-2">
          {footer}
        </p>

      </div>

    </div>
  );
}


/* =========================================================
   NORMAL STAFF SIGN IN
========================================================= */

export function SignIn({ portal }) {

  const t = THEME[portal];

  const { login } = useAuth();

  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState(null);

  const [busy, setBusy] = useState(false);


  const submit = async (e) => {

    e.preventDefault();

    setBusy(true);
    setError(null);

    try {

      await login({
        ...form,
        portal,
      });

      navigate(t.home, {
        replace: true,
      });

    } catch (err) {

      setError(
        err?.message ||
        "Unable to sign in."
      );

    } finally {

      setBusy(false);

    }

  };


  return (
    <Shell
      portal={portal}
      title="Sign in"
      subtitle="Use your staff account registered to this portal."
      footer={
        <>
          No staff account yet?{" "}

          <Link
            to={
              portal === "provider"
                ? "/hospital/staff/signup"
                : "/payer/staff/signup"
            }
            className={`font-medium ${t.link} hover:underline`}
          >
            Create one
          </Link>
        </>
      }
    >

      <form
        onSubmit={submit}
        className="space-y-4"
      >

        {error && (
          <Alert
            onDismiss={() => setError(null)}
          >
            {error}
          </Alert>
        )}


        <Field label="Work email">

          <input
            className="input"
            type="email"
            required
            autoFocus
            autoComplete="email"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
          />

        </Field>


        <Field label="Password">

          <input
            className="input"
            type="password"
            required
            autoComplete="current-password"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
          />

        </Field>


        <button
          type="submit"
          className={`btn w-full ${t.cta}`}
          disabled={busy}
        >
          {busy
            ? "Signing in…"
            : "Sign in"}
        </button>

      </form>

    </Shell>
  );
}


/* =========================================================
   ADMIN SIGN IN
========================================================= */

export function AdminSignIn({ portal }) {

  const t = THEME[portal];

  const adminRole =
    portal === "provider"
      ? "PROVIDER_ADMIN"
      : "PAYER_ADMIN";

  const adminHome =
    portal === "provider"
      ? "/hospital/admin"
      : "/payer/admin";

  const signupPath =
    portal === "provider"
      ? "/hospital/admin/signup"
      : "/payer/admin/signup";

  const { login, logout } = useAuth();

  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState(null);

  const [busy, setBusy] = useState(false);


  const submit = async (e) => {

    e.preventDefault();

    setBusy(true);
    setError(null);

    try {

      const user = await login({
        ...form,
        portal,
      });


      /* ---------------------------------------------
         Make sure this is actually an ADMIN account
      --------------------------------------------- */

      if (user?.role !== adminRole) {

        logout();

        const message =
          portal === "provider"
            ? "This account does not have hospital administrator access."
            : "This account does not have insurance administrator access.";

        setError(message);

        return;
      }


      navigate(adminHome, {
        replace: true,
      });

    } catch (err) {

      setError(
        err?.message ||
        "Unable to sign in."
      );

    } finally {

      setBusy(false);

    }

  };


  return (
    <Shell
      portal={portal}
      title="Admin sign in"
      subtitle={
        portal === "provider"
          ? "Sign in using your hospital administrator account."
          : "Sign in using your insurance administrator account."
      }
      footer={
        <>
          Don't have an admin account?{" "}

          <Link
            to={signupPath}
            className={`font-medium ${t.link} hover:underline`}
          >
            Create admin account
          </Link>
        </>
      }
    >

      <form
        onSubmit={submit}
        className="space-y-4"
      >

        {error && (
          <Alert
            onDismiss={() => setError(null)}
          >
            {error}
          </Alert>
        )}


        <Field label="Work email">

          <input
            className="input"
            type="email"
            required
            autoFocus
            autoComplete="email"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
          />

        </Field>


        <Field label="Password">

          <input
            className="input"
            type="password"
            required
            autoComplete="current-password"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
          />

        </Field>


        <button
          type="submit"
          className={`btn w-full ${t.cta}`}
          disabled={busy}
        >
          {busy
            ? "Signing in…"
            : "Sign in as admin"}
        </button>

      </form>

    </Shell>
  );
}


/* =========================================================
   HOSPITAL STAFF SIGN UP
========================================================= */

export function SignUpProvider() {

  const { signupProvider } = useAuth();

  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    organization_name: "",
  });

  const [error, setError] = useState(null);

  const [busy, setBusy] = useState(false);


  const submit = async (e) => {

    e.preventDefault();

    setBusy(true);
    setError(null);

    try {

      await signupProvider(form);

      navigate("/hospital", {
        replace: true,
      });

    } catch (err) {

      setError(
        err?.message ||
        "Unable to create account."
      );

    } finally {

      setBusy(false);

    }

  };


  return (
    <Shell
      portal="provider"
      title="Create a hospital staff account"
      subtitle="Create an account to submit authorization requests and manage hospital cases."
      footer={
        <>
          Already registered?{" "}

          <Link
            to="/hospital/staff/signin"
            className="font-medium text-provider hover:underline"
          >
            Sign in
          </Link>
        </>
      }
    >

      <form
        onSubmit={submit}
        className="space-y-4"
      >

        {error && (
          <Alert
            onDismiss={() => setError(null)}
          >
            {error}
          </Alert>
        )}


        <Field label="Full name">

          <input
            className="input"
            required
            autoFocus
            value={form.full_name}
            onChange={(e) =>
              setForm({
                ...form,
                full_name: e.target.value,
              })
            }
          />

        </Field>


        <Field label="Hospital or clinic">

          <input
            className="input"
            required
            value={form.organization_name}
            onChange={(e) =>
              setForm({
                ...form,
                organization_name: e.target.value,
              })
            }
          />

        </Field>


        <Field label="Work email">

          <input
            className="input"
            type="email"
            required
            autoComplete="email"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
          />

        </Field>


        <Field
          label="Password"
          hint="At least 8 characters."
        >

          <input
            className="input"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
          />

        </Field>


        <button
          type="submit"
          className="btn w-full bg-provider text-white border-provider hover:bg-provider-deep"
          disabled={busy}
        >
          {busy
            ? "Creating account…"
            : "Create account"}
        </button>

      </form>

    </Shell>
  );
}


/* =========================================================
   INSURANCE STAFF SIGN UP
========================================================= */
/* =========================================================
   INSURANCE / PAYER STAFF SIGN UP
========================================================= */

export function SignUpPayer() {
  const { signupPayer } = useAuth();
  const navigate = useNavigate();

  const [specialties, setSpecialties] = useState([]);

  const [form, setForm] = useState({
    full_name: "",
    organization_name: "",
    email: "",
    password: "",
    specialty: "",
    license_number: "",
    daily_capacity: 12,
  });

  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  /* ---------------------------------------------------------
     LOAD SPECIALTIES FROM BACKEND
  --------------------------------------------------------- */

  useEffect(() => {
    api
      .get("/api/auth/specialties")
      .then((response) => {
        const list = response?.specialties || [];

        setSpecialties(list);

        if (list.length > 0) {
          setForm((current) => ({
            ...current,
            specialty: current.specialty || list[0],
          }));
        }
      })
      .catch(() => {
        setError(
          "Unable to load specialties. Please make sure the backend is running."
        );
      });
  }, []);

  /* ---------------------------------------------------------
     SUBMIT
  --------------------------------------------------------- */

  const submit = async (e) => {
    e.preventDefault();

    setBusy(true);
    setError(null);

    if (!form.specialty) {
      setError("Please select a review specialty.");
      setBusy(false);
      return;
    }

    if (!form.license_number.trim()) {
      setError("Please enter your license number.");
      setBusy(false);
      return;
    }

    try {
      await signupPayer({
        full_name: form.full_name.trim(),
        organization_name: form.organization_name.trim(),
        email: form.email.trim(),
        password: form.password,

        specialty: form.specialty,

        license_number:
          form.license_number.trim(),

        daily_capacity:
          Number(form.daily_capacity),
      });

      /* ---------------------------------------------
         SUCCESS → INSURANCE STAFF DASHBOARD
      --------------------------------------------- */

      navigate("/payer", {
        replace: true,
      });

    } catch (err) {
      setError(
        err?.message ||
        "Unable to create insurance staff account."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Shell
      portal="payer"
      title="Create an insurance staff account"
      subtitle="Create an account to review authorization cases and handle appeals."
      footer={
        <>
          Already registered?{" "}
          <Link
            to="/payer/staff/signin"
            className="font-medium text-payer hover:underline"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form
        onSubmit={submit}
        className="space-y-4"
      >

        {/* ERROR */}

        {error && (
          <Alert
            onDismiss={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        {/* FULL NAME */}

        <Field label="Full name">
          <input
            className="input"
            required
            autoFocus
            value={form.full_name}
            onChange={(e) =>
              setForm({
                ...form,
                full_name: e.target.value,
              })
            }
          />
        </Field>

        {/* ORGANIZATION */}

        <Field label="Insurance organization">
          <input
            className="input"
            required
            value={form.organization_name}
            onChange={(e) =>
              setForm({
                ...form,
                organization_name:
                  e.target.value,
              })
            }
          />
        </Field>

        {/* SPECIALTY */}

        <Field
          label="Review specialty"
          hint="Cases matching this specialty will be routed to you."
        >
          <select
            className="input"
            required
            value={form.specialty}
            onChange={(e) =>
              setForm({
                ...form,
                specialty: e.target.value,
              })
            }
          >
            <option value="">
              Select specialty
            </option>

            {specialties.map((specialty) => (
              <option
                key={specialty}
                value={specialty}
              >
                {specialty}
              </option>
            ))}
          </select>
        </Field>

        {/* LICENSE + CAPACITY */}

        <div className="grid grid-cols-2 gap-3">

          <Field label="License number">
            <input
              className="input"
              required
              value={form.license_number}
              onChange={(e) =>
                setForm({
                  ...form,
                  license_number:
                    e.target.value,
                })
              }
            />
          </Field>

          <Field
            label="Cases per day"
            hint="Maximum cases you can review."
          >
            <input
              className="input"
              type="number"
              min="1"
              max="100"
              required
              value={form.daily_capacity}
              onChange={(e) =>
                setForm({
                  ...form,
                  daily_capacity:
                    e.target.value,
                })
              }
            />
          </Field>

        </div>

        {/* EMAIL */}

        <Field label="Work email">
          <input
            className="input"
            type="email"
            required
            autoComplete="email"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
          />
        </Field>

        {/* PASSWORD */}

        <Field
          label="Password"
          hint="At least 8 characters."
        >
          <input
            className="input"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
          />
        </Field>

        {/* SUBMIT */}

        <button
          type="submit"
          className="btn w-full bg-payer text-white border-payer hover:bg-payer-deep"
          disabled={busy}
        >
          {busy
            ? "Creating account…"
            : "Create account"}
        </button>

      </form>
    </Shell>
  );
}




 


         


     
      
      

/* =========================================================
   ADMIN ACCOUNT CREATION
========================================================= */

export function SignUpAdmin({ portal }) {

  const t = THEME[portal];

  const { signupAdmin } = useAuth();

  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    organization_name: "",
  });

  const [error, setError] = useState(null);

  const [busy, setBusy] = useState(false);


  const isHospital = portal === "provider";


  const submit = async (e) => {

    e.preventDefault();

    setBusy(true);
    setError(null);

    try {

      await signupAdmin({
        ...form,
        portal,
      });

      navigate(
        isHospital
          ? "/hospital/admin"
          : "/payer/admin",
        {
          replace: true,
        }
      );

    } catch (err) {

      setError(
        err?.message ||
        "Unable to create admin account."
      );

    } finally {

      setBusy(false);

    }

  };


  return (
    <Shell
      portal={portal}
      title={
        isHospital
          ? "Create hospital admin account"
          : "Create insurance admin account"
      }
      subtitle={
        isHospital
          ? "Create an administrator account to access hospital-wide operations and audit information."
          : "Create an administrator account to access insurance-wide operations and audit information."
      }
      footer={
        <>
          Already have an admin account?{" "}

          <Link
            to={
              isHospital
                ? "/hospital/admin/signin"
                : "/payer/admin/signin"
            }
            className={`font-medium ${t.link} hover:underline`}
          >
            Sign in
          </Link>
        </>
      }
    >

      <form
        onSubmit={submit}
        className="space-y-4"
      >

        {error && (
          <Alert
            onDismiss={() => setError(null)}
          >
            {error}
          </Alert>
        )}


        <Field label="Full name">

          <input
            className="input"
            required
            autoFocus
            value={form.full_name}
            onChange={(e) =>
              setForm({
                ...form,
                full_name: e.target.value,
              })
            }
          />

        </Field>


        <Field
          label={
            isHospital
              ? "Hospital or clinic"
              : "Insurance organization"
          }
        >

          <input
            className="input"
            required
            value={form.organization_name}
            onChange={(e) =>
              setForm({
                ...form,
                organization_name: e.target.value,
              })
            }
          />

        </Field>


        <Field label="Work email">

          <input
            className="input"
            type="email"
            required
            autoComplete="email"
            value={form.email}
            onChange={(e) =>
              setForm({
                ...form,
                email: e.target.value,
              })
            }
          />

        </Field>


        <Field
          label="Password"
          hint="At least 8 characters."
        >

          <input
            className="input"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={form.password}
            onChange={(e) =>
              setForm({
                ...form,
                password: e.target.value,
              })
            }
          />

        </Field>


        <button
          type="submit"
          className={`btn w-full ${t.cta}`}
          disabled={busy}
        >
          {busy
            ? "Creating admin account…"
            : "Create admin account"}
        </button>

      </form>

    </Shell>
  );
}