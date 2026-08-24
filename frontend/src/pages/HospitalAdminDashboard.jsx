import { useEffect, useState } from "react";

import {
  Activity,
  CheckCircle2,
  Clock3,
  FileText,
  History,
  LogIn,
  Upload,
  Users,
  XCircle,
} from "lucide-react";

import { api } from "../lib/api";

import {
  Alert,
  Card,
  Empty,
  Spinner,
  Status,
  fmtDate,
} from "../components/ui";


export default function HospitalAdminDashboard() {

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const loadDashboard = async () => {

    setError(null);

    try {

      const result = await api.get(
        "/api/admin/dashboard"
      );

      setData(result);

    } catch (err) {

      setError(
        err.message ||
        "Unable to load hospital administration data."
      );

    }

  };


  useEffect(() => {

    loadDashboard();

    const interval = setInterval(
      loadDashboard,
      15000
    );

    return () => clearInterval(interval);

  }, []);


  if (error && !data) {

    return (
      <div className="mx-auto max-w-[1100px] p-6">

        <Alert>
          {error}
        </Alert>

      </div>
    );

  }


  if (!data) {

    return (
      <div className="mx-auto max-w-[1100px] p-10">

        <Spinner
          label="Loading hospital administration"
        />

      </div>
    );

  }


  const overview =
    data.overview || {};

  const staff =
    data.staff || [];

  const cases =
    data.cases || [];

  const documents =
    data.documents || [];

  const activity =
    data.staff_activity || [];

  const logins =
    data.login_history || [];

  const audits =
    data.audit_logs || [];


  return (
    <div className="mx-auto max-w-[1100px] space-y-6">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div>

        <div className="eyebrow">
          Hospital administration
        </div>

        <h1 className="mt-1 text-2xl font-semibold">
          Administration dashboard
        </h1>

        <p className="mt-1.5 text-[13px] text-ink-2">
          Monitor staff activity, authorization cases,
          uploaded documents and the complete hospital
          audit history.
        </p>

      </div>


      {error && (
        <Alert>
          {error}
        </Alert>
      )}


      {/* =====================================================
          ORGANIZATION
      ===================================================== */}

      <Card>

        <div className="flex flex-wrap items-center justify-between gap-4">

          <div>

            <div className="eyebrow">
              Organization
            </div>

            <h2 className="mt-1 text-lg font-semibold">
              {data.organization?.name}
            </h2>

            <p className="mt-1 text-[13px] text-ink-2">
              Hospital / Provider organization
            </p>

          </div>

          <div className="chip border-provider-line bg-provider-soft text-provider">
            Hospital Admin
          </div>

        </div>

      </Card>


      {/* =====================================================
          OVERVIEW
      ===================================================== */}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <OverviewCard
          icon={Users}
          label="Staff members"
          value={overview.total_staff}
          description="Registered hospital staff"
        />

        <OverviewCard
          icon={FileText}
          label="Cases submitted"
          value={overview.total_cases}
          description="Authorization requests"
        />

        <OverviewCard
          icon={CheckCircle2}
          label="Cases completed"
          value={overview.completed_cases}
          description="Processed authorization cases"
        />

        <OverviewCard
          icon={Activity}
          label="Audit events"
          value={overview.total_audit_events}
          description="Recorded staff activity"
        />

      </div>


      {/* =====================================================
          SECONDARY OVERVIEW
      ===================================================== */}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <SmallMetric
          icon={Clock3}
          label="Pending review"
          value={overview.pending_cases}
        />

        <SmallMetric
          icon={CheckCircle2}
          label="Approved"
          value={overview.approved_cases}
        />

        <SmallMetric
          icon={XCircle}
          label="Denied"
          value={overview.denied_cases}
        />

        <SmallMetric
          icon={Upload}
          label="Documents"
          value={overview.total_documents}
        />

      </div>


      {/* =====================================================
          STAFF MEMBERS
      ===================================================== */}

      <Card
        eyebrow="People"
        title="Hospital staff"
        bodyClass="p-0"
      >

        {staff.length === 0 ? (

          <Empty
            icon={Users}
            title="No staff members"
          >
            Staff accounts will appear here after
            registration.
          </Empty>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full">

              <thead>

                <tr>

                  <th className="th">
                    Staff member
                  </th>

                  <th className="th">
                    Email
                  </th>

                  <th className="th">
                    Status
                  </th>

                  <th className="th">
                    Last login
                  </th>

                  <th className="th">
                    Registered
                  </th>

                </tr>

              </thead>


              <tbody>

                {staff.map((member) => (

                  <tr key={member.id}>

                    <td className="td">

                      <div className="font-medium">
                        {member.full_name}
                      </div>

                      <div className="text-2xs text-ink-3">
                        Hospital staff
                      </div>

                    </td>


                    <td className="td">
                      {member.email}
                    </td>


                    <td className="td">

                      {member.last_login_at ? (

                        <span className="chip bg-approve/10 text-approve">
                          Active
                        </span>

                      ) : (

                        <span className="chip bg-canvas text-ink-3">
                          Never logged in
                        </span>

                      )}

                    </td>


                    <td className="td text-2xs text-ink-3">
                      {member.last_login_at
                        ? fmtDate(member.last_login_at)
                        : "—"}
                    </td>


                    <td className="td text-2xs text-ink-3">
                      {fmtDate(member.created_at)}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </Card>


      {/* =====================================================
          UPLOADED DOCUMENTS
      ===================================================== */}

      <Card
        eyebrow="Documents"
        title="Documents uploaded by staff"
        bodyClass="p-0"
      >

        {documents.length === 0 ? (

          <Empty
            icon={Upload}
            title="No documents uploaded"
          >
            Documents uploaded by hospital staff
            will appear here.
          </Empty>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full">

              <thead>

                <tr>

                  <th className="th">
                    File
                  </th>

                  <th className="th">
                    Request
                  </th>

                  <th className="th">
                    Pages
                  </th>

                  <th className="th">
                    Extraction
                  </th>

                  <th className="th">
                    Uploaded
                  </th>

                </tr>

              </thead>


              <tbody>

                {documents.map((document) => (

                  <tr key={document.id}>

                    <td className="td">

                      <div className="flex items-center gap-2">

                        <FileText
                          size={16}
                          className="text-provider"
                        />

                        <div>
                          <div className="font-medium">
                            {document.filename}
                          </div>
                          {document.uploaded_by_name && (
                            <div className="text-2xs text-ink-3">
                              Uploaded by {document.uploaded_by_name}
                            </div>
                          )}
                        </div>

                      </div>

                    </td>


                    <td className="td num text-2xs">

                      {document.request_id
                        ? document.request_id.slice(0, 8)
                        : "Not linked"}

                    </td>


                    <td className="td num">
                      {document.page_count ?? "—"}
                    </td>


                    <td className="td">

                      {document.extraction_confidence != null
                        ? `${Math.round(
                            document.extraction_confidence * 100
                          )}%`
                        : "—"}

                    </td>


                    <td className="td text-2xs text-ink-3">
                      {fmtDate(document.created_at)}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </Card>


      {/* =====================================================
          CASE HISTORY
      ===================================================== */}

      <Card
        eyebrow="Authorization"
        title="Staff-submitted cases"
        bodyClass="p-0"
      >

        {cases.length === 0 ? (

          <Empty
            icon={FileText}
            title="No cases submitted"
          >
            Cases created by hospital staff will
            appear here.
          </Empty>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full">

              <thead>

                <tr>

                  <th className="th">
                    Case
                  </th>

                  <th className="th">
                    Staff
                  </th>

                  <th className="th">
                    Diagnosis
                  </th>

                  <th className="th">
                    Treatment
                  </th>

                  <th className="th">
                    Status
                  </th>

                  <th className="th">
                    Submitted
                  </th>

                </tr>

              </thead>


              <tbody>

                {cases.map((item) => (

                  <tr key={item.id}>

                    <td className="td num text-2xs">
                      {item.case_number}
                    </td>


                    <td className="td">

                      {item.created_by ? (
                        <>
                          <div className="font-medium">
                            {item.created_by.name}
                          </div>

                          <div className="text-2xs text-ink-3">
                            {item.created_by.email}
                          </div>
                        </>
                      ) : (
                        "—"
                      )}

                    </td>


                    <td className="td">

                      <div className="font-medium">
                        {item.diagnosis || "—"}
                      </div>

                      <div className="text-2xs text-ink-3">
                        {item.disease_severity || ""}
                      </div>

                    </td>


                    <td className="td">
                      {item.requested_treatment || "—"}
                    </td>


                    <td className="td">

                      <Status
                        value={
                          item.status ||
                          "SUBMITTED"
                        }
                      />

                    </td>


                    <td className="td text-2xs text-ink-3">
                      {fmtDate(item.created_at)}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </Card>


      {/* =====================================================
          LOGIN HISTORY
      ===================================================== */}

      <Card
        eyebrow="Security"
        title="Staff login history"
      >

        {logins.length === 0 ? (

          <Empty
            icon={LogIn}
            title="No login history"
          >
            Staff login activity will appear here.
          </Empty>

        ) : (

          <div className="space-y-3">

            {logins.slice(0, 20).map((event) => (

              <div
                key={event.id}
                className="flex items-center justify-between gap-4 rounded-lg border border-rule bg-canvas px-4 py-3"
              >

                <div className="flex items-center gap-3">

                  <div className="rounded-lg bg-provider-soft p-2">
                    <LogIn
                      size={16}
                      className="text-provider"
                    />
                  </div>

                  <div>

                    <div className="text-sm font-medium">
                      {event.actor_email}
                    </div>

                    <div className="text-2xs text-ink-3">
                      Staff login
                    </div>

                  </div>

                </div>


                <div className="text-2xs text-ink-3">
                  {fmtDate(event.created_at)}
                </div>

              </div>

            ))}

          </div>

        )}

      </Card>


      {/* =====================================================
          AUDIT LOGS
      ===================================================== */}

      <Card
        eyebrow="Compliance"
        title="Audit logs"
      >

        {audits.length === 0 ? (

          <Empty
            icon={History}
            title="No audit activity yet"
          >
            Staff actions will appear here as users
            log in, upload documents and submit cases.
          </Empty>

        ) : (

          <div className="divide-y divide-rule">

            {audits.slice(0, 50).map((event) => (

              <div
                key={event.id}
                className="py-4"
              >

                <div className="flex items-start justify-between gap-4">

                  <div>

                    <div className="flex items-center gap-2">

                      <span className="num text-2xs font-semibold uppercase tracking-wider">
                        {String(event.action || "")
                          .replace(/_/g, " ")}
                      </span>

                    </div>

                    {event.actor_email && (
                      <div className="mt-1 text-2xs text-ink-3">
                        {event.actor_email}
                      </div>
                    )}

                    {event.detail && (
                      <pre className="mt-2 overflow-x-auto rounded-md bg-canvas p-2 text-2xs text-ink-2">
                        {JSON.stringify(
                          event.detail,
                          null,
                          2
                        )}
                      </pre>
                    )}

                  </div>


                  <span className="shrink-0 text-2xs text-ink-3">
                    {fmtDate(event.created_at)}
                  </span>

                </div>

              </div>

            ))}

          </div>

        )}

      </Card>


      {/* =====================================================
          ORGANIZATION ACTIVITY
      ===================================================== */}

      <Card
        eyebrow="Organization"
        title="Recent organization activity"
      >

        {activity.length === 0 ? (

          <Empty
            icon={Activity}
            title="No organization activity"
          />

        ) : (

          <div className="space-y-2">

            {activity.slice(0, 20).map((event) => (

              <div
                key={event.id}
                className="flex items-center justify-between rounded-lg border border-rule px-3 py-2.5"
              >

                <div>

                  <div className="text-sm font-medium">
                    {String(event.action || "")
                      .replace(/_/g, " ")}
                  </div>

                  <div className="text-2xs text-ink-3">
                    {event.actor_email || "System"}
                  </div>

                </div>


                <span className="text-2xs text-ink-3">
                  {fmtDate(event.created_at)}
                </span>

              </div>

            ))}

          </div>

        )}

      </Card>

    </div>
  );
}


/* ============================================================
   OVERVIEW CARD
============================================================ */

function OverviewCard({
  icon: Icon,
  label,
  value,
  description,
}) {

  return (
    <div className="rounded-2xl border border-rule bg-white p-5 shadow-card">

      <div className="flex items-start justify-between">

        <div>

          <div className="eyebrow">
            {label}
          </div>

          <div className="mt-2 text-3xl font-semibold">
            {value ?? 0}
          </div>

          <p className="mt-1 text-2xs text-ink-3">
            {description}
          </p>

        </div>


        <div className="grid h-10 w-10 place-items-center rounded-xl bg-provider-soft">

          <Icon
            size={18}
            className="text-provider"
          />

        </div>

      </div>

    </div>
  );
}


/* ============================================================
   SMALL METRIC
============================================================ */

function SmallMetric({
  icon: Icon,
  label,
  value,
}) {

  return (
    <div className="rounded-xl border border-rule bg-white px-4 py-3">

      <div className="flex items-center gap-3">

        <Icon
          size={17}
          className="text-provider"
        />

        <div>

          <div className="text-2xs text-ink-3">
            {label}
          </div>

          <div className="num text-lg font-semibold">
            {value ?? 0}
          </div>

        </div>

      </div>

    </div>
  );
}