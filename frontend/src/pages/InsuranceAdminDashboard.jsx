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


export default function InsuranceAdminDashboard() {

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);


  const load = async () => {

    setError(null);

    try {

      const result =
        await api.get("/api/admin/dashboard");

      setData(result);

    } catch (err) {

      setError(
        err.message ||
        "Unable to load insurance administration data."
      );

    }

  };


  useEffect(() => {

    load();

    const timer = setInterval(
      load,
      15000
    );

    return () => clearInterval(timer);

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
          label="Loading insurance administration"
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

  const logins =
    data.login_history || [];

  const audits =
    data.audit_logs || [];


  return (
    <div className="mx-auto max-w-[1100px] space-y-6">

      {/* HEADER */}

      <div>

        <div className="eyebrow">
          Insurance administration
        </div>

        <h1 className="mt-1 text-2xl font-semibold">
          Administration dashboard
        </h1>

        <p className="mt-1.5 text-[13px] text-ink-2">
          Monitor reviewer activity, authorization
          cases, documents and insurance audit history.
        </p>

      </div>


      {error && (
        <Alert>
          {error}
        </Alert>
      )}


      {/* ORGANIZATION */}

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
              Insurance / Payer organization
            </p>

          </div>

          <div className="chip border-payer-line bg-payer-soft text-payer">
            Insurance Admin
          </div>

        </div>

      </Card>


      {/* OVERVIEW */}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <Metric
          icon={Users}
          label="Reviewers"
          value={overview.total_staff}
          description="Registered insurance staff"
        />

        <Metric
          icon={FileText}
          label="Cases"
          value={overview.total_cases}
          description="Cases assigned to reviewers"
        />

        <Metric
          icon={CheckCircle2}
          label="Completed"
          value={overview.completed_cases}
          description="Processed cases"
        />

        <Metric
          icon={Activity}
          label="Audit events"
          value={overview.total_audit_events}
          description="Recorded activity"
        />

      </div>


      {/* STATUS */}

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


      {/* REVIEWERS */}

      <Card
        eyebrow="People"
        title="Reviewer activity"
        bodyClass="p-0"
      >

        {staff.length === 0 ? (

          <Empty
            icon={Users}
            title="No reviewers found"
          >
            Insurance reviewer accounts will appear
            here after registration.
          </Empty>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full">

              <thead>

                <tr>

                  <th className="th">
                    Reviewer
                  </th>

                  <th className="th">
                    Email
                  </th>

                  <th className="th">
                    Specialty
                  </th>

                  <th className="th">
                    Availability
                  </th>

                  <th className="th">
                    Last login
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
                        Insurance reviewer
                      </div>

                    </td>


                    <td className="td">
                      {member.email}
                    </td>


                    <td className="td">
                      {member.specialty || "—"}
                    </td>


                    <td className="td">

                      {member.is_available ? (

                        <span className="chip bg-approve/10 text-approve">
                          Available
                        </span>

                      ) : (

                        <span className="chip bg-deny/10 text-deny">
                          Unavailable
                        </span>

                      )}

                    </td>


                    <td className="td text-2xs text-ink-3">
                      {member.last_login_at
                        ? fmtDate(member.last_login_at)
                        : "Never"}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </Card>


      {/* CASE HISTORY */}

      <Card
        eyebrow="Cases"
        title="Reviewer case history"
        bodyClass="p-0"
      >

        {cases.length === 0 ? (

          <Empty
            icon={FileText}
            title="No cases yet"
          >
            Cases assigned to insurance reviewers will
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
                    Submitted by
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
                      {item.diagnosis || "—"}
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


      {/* DOCUMENTS */}

      <Card
        eyebrow="Documents"
        title="Uploaded documentation"
        bodyClass="p-0"
      >

        {documents.length === 0 ? (

          <Empty
            icon={Upload}
            title="No documents"
          >
            Uploaded documentation will appear here.
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
                          className="text-payer"
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


                    <td className="td">
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


      {/* LOGIN HISTORY */}

      <Card
        eyebrow="Security"
        title="Reviewer login history"
      >

        {logins.length === 0 ? (

          <Empty
            icon={LogIn}
            title="No login history"
          />

        ) : (

          <div className="space-y-3">

            {logins.slice(0, 20).map((event) => (

              <div
                key={event.id}
                className="flex items-center justify-between rounded-lg border border-rule bg-canvas px-4 py-3"
              >

                <div className="flex items-center gap-3">

                  <div className="rounded-lg bg-payer-soft p-2">

                    <LogIn
                      size={16}
                      className="text-payer"
                    />

                  </div>

                  <div>

                    <div className="text-sm font-medium">
                      {event.actor_email}
                    </div>

                    <div className="text-2xs text-ink-3">
                      Reviewer login
                    </div>

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


      {/* AUDIT */}

      <Card
        eyebrow="Compliance"
        title="Insurance audit logs"
      >

        {audits.length === 0 ? (

          <Empty
            icon={History}
            title="No audit events yet"
          />

        ) : (

          <div className="divide-y divide-rule">

            {audits.slice(0, 50).map((event) => (

              <div
                key={event.id}
                className="py-4"
              >

                <div className="flex items-start justify-between gap-4">

                  <div>

                    <div className="num text-2xs font-semibold uppercase tracking-wider">
                      {String(event.action || "")
                        .replace(/_/g, " ")}
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

    </div>
  );
}


/* ============================================================
   METRIC
============================================================ */

function Metric({
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


        <div className="grid h-10 w-10 place-items-center rounded-xl bg-payer-soft">

          <Icon
            size={18}
            className="text-payer"
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
          className="text-payer"
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