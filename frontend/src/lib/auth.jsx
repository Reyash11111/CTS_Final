import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import {
  Navigate,
  useLocation,
} from "react-router-dom";

import { api } from "./api";


const AuthContext = createContext(null);


/* =========================================================
   AUTH PROVIDER
========================================================= */

export function AuthProvider({ children }) {

  const [user, setUser] = useState(() => {

    const raw = localStorage.getItem("pa_user");

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw);
    } catch {
      localStorage.removeItem("pa_user");
      return null;
    }

  });


  /* =======================================================
     PERSIST LOGIN
  ======================================================= */

  const persist = useCallback((res) => {

    if (!res?.access_token || !res?.user) {
      throw new Error("Invalid authentication response.");
    }

    localStorage.setItem(
      "pa_token",
      res.access_token
    );

    localStorage.setItem(
      "pa_user",
      JSON.stringify(res.user)
    );

    setUser(res.user);

    return res.user;

  }, []);


  /* =======================================================
     AUTH CONTEXT
  ======================================================= */

  const value = useMemo(
    () => ({

      user,


      /* ===================================================
         ROLE HELPERS
      =================================================== */

      isProvider:
        user?.role === "PROVIDER_STAFF",

      isProviderAdmin:
        user?.role === "PROVIDER_ADMIN",

      isPayer:
        user?.role === "PAYER_REVIEWER",

      isPayerAdmin:
        user?.role === "PAYER_ADMIN",

      isAdmin:
        user?.role === "PROVIDER_ADMIN" ||
        user?.role === "PAYER_ADMIN",


      /* ===================================================
         GENERIC LOGIN
      =================================================== */

      login: async (payload) => {

        const response = await api.post(
          "/api/auth/login",
          payload
        );

        return persist(response);

      },


      /* ===================================================
         HOSPITAL STAFF SIGNUP
      =================================================== */

      signupProvider: async (payload) => {

        const response = await api.post(
          "/api/auth/signup/provider",
          payload
        );

        return persist(response);

      },


      /* ===================================================
         INSURANCE STAFF SIGNUP
      =================================================== */

      signupPayer: async (payload) => {

        const response = await api.post(
          "/api/auth/signup/payer",
          payload
        );

        return persist(response);

      },


      /* ===================================================
         HOSPITAL ADMIN SIGNUP
      =================================================== */

      signupProviderAdmin: async (payload) => {

        const response = await api.post(
          "/api/auth/signup/provider/admin",
          payload
        );

        return persist(response);

      },


      /* ===================================================
         INSURANCE ADMIN SIGNUP
      =================================================== */

      signupPayerAdmin: async (payload) => {

        const response = await api.post(
          "/api/auth/signup/payer/admin",
          payload
        );

        return persist(response);

      },


      /* ===================================================
         GENERIC ADMIN SIGNUP

         Used by pages/Auth.jsx for both admin portals.
      =================================================== */

      signupAdmin: async (payload) => {

        if (!payload?.portal) {
          throw new Error("Invalid admin portal.");
        }

        const endpoint =
          payload.portal === "provider"
            ? "/api/auth/signup/provider/admin"
            : payload.portal === "payer"
              ? "/api/auth/signup/payer/admin"
              : null;

        if (!endpoint) {
          throw new Error("Invalid admin portal.");
        }

        const response = await api.post(endpoint, {
          full_name: payload.full_name,
          email: payload.email,
          password: payload.password,
          organization_name: payload.organization_name,
        });

        return persist(response);

      },


      /* ===================================================
         REFRESH CURRENT USER
      =================================================== */

      refresh: async () => {

        const me = await api.get(
          "/api/auth/me"
        );

        localStorage.setItem(
          "pa_user",
          JSON.stringify(me)
        );

        setUser(me);

        return me;

      },


      /* ===================================================
         LOGOUT
      =================================================== */

      logout: () => {

        localStorage.removeItem(
          "pa_token"
        );

        localStorage.removeItem(
          "pa_user"
        );

        setUser(null);

      },

    }),

    [user, persist]
  );


  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}


/* =========================================================
   USE AUTH
========================================================= */

export function useAuth() {

  const ctx = useContext(
    AuthContext
  );

  if (!ctx) {

    throw new Error(
      "useAuth must be used inside AuthProvider"
    );

  }

  return ctx;
}


/* =========================================================
   ROLE PROTECTION
========================================================= */

export function RequireRole({
  role,
  children,
}) {

  const { user } = useAuth();

  const location = useLocation();


  /* =======================================================
     NOT LOGGED IN
  ======================================================= */

  if (!user) {

    const loginRoutes = {

      PROVIDER_STAFF:
        "/hospital/staff/signin",

      PROVIDER_ADMIN:
        "/hospital/admin/signin",

      PAYER_REVIEWER:
        "/payer/staff/signin",

      PAYER_ADMIN:
        "/payer/admin/signin",

    };


    return (
      <Navigate
        to={
          loginRoutes[role] || "/"
        }
        state={{
          from: location,
        }}
        replace
      />
    );

  }


  /* =======================================================
     CORRECT ROLE
  ======================================================= */

  if (user.role === role) {

    return children;

  }


  /* =======================================================
     WRONG ROLE
  ======================================================= */

  switch (user.role) {

    case "PROVIDER_ADMIN":

      return (
        <Navigate
          to="/hospital/admin"
          replace
        />
      );


    case "PROVIDER_STAFF":

      return (
        <Navigate
          to="/hospital"
          replace
        />
      );


    case "PAYER_ADMIN":

      return (
        <Navigate
          to="/payer/admin"
          replace
        />
      );


    case "PAYER_REVIEWER":

      return (
        <Navigate
          to="/payer"
          replace
        />
      );


    default:

      return (
        <Navigate
          to="/"
          replace
        />
      );

  }

}