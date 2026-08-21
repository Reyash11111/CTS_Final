import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Clock3,
  Inbox,
  RefreshCw,
  ShieldAlert,
  UserCheck,
  ChevronRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

const PRIORITY_ORDER = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
};

function getPriority(item) {
  return (
    item?.review_priority ||
    item?.priority ||
    item?.severity_level ||
    "LOW"
  ).toUpperCase();
}

function getSeverity(item) {
  const value =
    item?.severity_score ??
    item?.severity ??
    item?.validation?.severity_score ??
    0;

  const number = Number(value);

  if (Number.isNaN(number)) {
    return 0;
  }

  // Supports both 0.95 and 95
  return number <= 1 ? Math.round(number * 100) : Math.round(number);
}

function getStatus(item) {
  return (
    item?.status ||
    item?.review_status ||
    "PENDING"
  ).toUpperCase();
}

function priorityStyles(priority) {
  switch (priority) {
    case "CRITICAL":
      return {
        badge: "border-red-200 bg-red-50 text-red-700",
        dot: "bg-red-600",
        text: "text-red-700",
      };

    case "HIGH":
      return {
        badge: "border-orange-200 bg-orange-50 text-orange-700",
        dot: "bg-orange-500",
        text: "text-orange-700",
      };

    case "MEDIUM":
      return {
        badge: "border-amber-200 bg-amber-50 text-amber-700",
        dot: "bg-amber-500",
        text: "text-amber-700",
      };

    default:
      return {
        badge: "border-slate-200 bg-slate-50 text-slate-600",
        dot: "bg-slate-400",
        text: "text-slate-600",
      };
  }
}

function formatDate(value) {
  if (!value) return "Recently submitted";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Recently submitted";
  }

  return date.toLocaleString();
}

export default function ReviewQueue() {
  const navigate = useNavigate();

  /*
   * IMPORTANT:
   * Default is now "unassigned".
   *
   * A newly created human-review case will normally have
   * assigned_to = null, so it must appear here.
   */
  const [activeTab, setActiveTab] = useState("unassigned");

  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadQueue = async () => {
    try {
      setError("");

      const response = await api.get("/api/review/queue");

      /*
       * Supports:
       * response.data
       * response.data.items
       * response.data.queue
       * direct array
       */
      const data = response?.data ?? response;

      let items = [];

      if (Array.isArray(data)) {
        items = data;
      } else if (Array.isArray(data?.items)) {
        items = data.items;
      } else if (Array.isArray(data?.queue)) {
        items = data.queue;
      } else if (Array.isArray(data?.results)) {
        items = data.results;
      }

      setQueue(items);
    } catch (err) {
      console.error("Failed to load review queue:", err);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to load the human review queue."
      );

      setQueue([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadQueue();

    /*
     * Automatically refresh the queue.
     *
     * This is useful because a hospital may submit a request
     * while the reviewer page is already open.
     */
    const interval = setInterval(() => {
      loadQueue();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadQueue();
  };

  /*
   * Sort by clinical priority:
   *
   * CRITICAL
   * HIGH
   * MEDIUM
   * LOW
   *
   * Within the same priority, higher severity appears first.
   */
  const sortedQueue = useMemo(() => {
    return [...queue].sort((a, b) => {
      const priorityA = getPriority(a);
      const priorityB = getPriority(b);

      const priorityDifference =
        (PRIORITY_ORDER[priorityB] || 0) -
        (PRIORITY_ORDER[priorityA] || 0);

      if (priorityDifference !== 0) {
        return priorityDifference;
      }

      return getSeverity(b) - getSeverity(a);
    });
  }, [queue]);

  /*
   * Filter according to the selected queue.
   */
  const visibleQueue = useMemo(() => {
    if (activeTab === "everything") {
      return sortedQueue;
    }

    if (activeTab === "unassigned") {
      return sortedQueue.filter((item) => {
        const assigned =
          item?.assigned_to ??
          item?.assigned_to_id ??
          item?.reviewer_id ??
          item?.reviewer;

        return !assigned;
      });
    }

    if (activeTab === "assigned") {
      return sortedQueue.filter((item) => {
        const assigned =
          item?.assigned_to ??
          item?.assigned_to_id ??
          item?.reviewer_id ??
          item?.reviewer;

        return Boolean(assigned);
      });
    }

    return sortedQueue;
  }, [sortedQueue, activeTab]);

  const criticalCount = queue.filter(
    (item) => getPriority(item) === "CRITICAL"
  ).length;

  const highCount = queue.filter(
    (item) => getPriority(item) === "HIGH"
  ).length;

  return (
    <div className="space-y-6">

      {/* HEADER */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">

        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[.18em] text-ink-3">
            Insurance organization
          </div>

          <div className="mt-1 flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">
              Review queue
            </h1>

            {criticalCount > 0 && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-[11px] font-bold text-red-700">
                <ShieldAlert size={13} />
                {criticalCount} Critical
              </span>
            )}
          </div>

          <p className="mt-1 text-sm text-ink-2">
            Ordered by clinical urgency, not arrival time.
            The most severe cases surface first.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-rule bg-white px-4 py-2.5 text-xs font-semibold text-ink-2 transition hover:bg-slate-50 disabled:opacity-60"
        >
          <RefreshCw
            size={15}
            className={refreshing ? "animate-spin" : ""}
          />

          Refresh
        </button>
      </div>


      {/* PRIORITY SUMMARY */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">

        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <div className="flex items-center gap-2">
            <ShieldAlert
              size={17}
              className="text-red-600"
            />

            <span className="text-xs font-semibold text-red-700">
              Critical
            </span>
          </div>

          <div className="mt-2 text-2xl font-bold text-red-700">
            {criticalCount}
          </div>

          <div className="mt-1 text-[11px] text-red-600">
            Immediate review
          </div>
        </div>


        <div className="rounded-xl border border-orange-200 bg-orange-50 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle
              size={17}
              className="text-orange-600"
            />

            <span className="text-xs font-semibold text-orange-700">
              High
            </span>
          </div>

          <div className="mt-2 text-2xl font-bold text-orange-700">
            {highCount}
          </div>

          <div className="mt-1 text-[11px] text-orange-600">
            Priority review
          </div>
        </div>


        <div className="rounded-xl border border-rule bg-white p-4">
          <div className="flex items-center gap-2">
            <Clock3
              size={17}
              className="text-provider"
            />

            <span className="text-xs font-semibold text-ink-2">
              Total pending
            </span>
          </div>

          <div className="mt-2 text-2xl font-bold">
            {queue.length}
          </div>

          <div className="mt-1 text-[11px] text-ink-3">
            Awaiting human decision
          </div>
        </div>

      </div>


      {/* TABS */}
      <div className="flex flex-wrap gap-2">

        <button
          onClick={() => setActiveTab("unassigned")}
          className={`rounded-lg px-4 py-2.5 text-xs font-semibold transition ${
            activeTab === "unassigned"
              ? "bg-ink text-white"
              : "border border-rule bg-white text-ink-2 hover:bg-slate-50"
          }`}
        >
          Unassigned
        </button>

        <button
          onClick={() => setActiveTab("assigned")}
          className={`rounded-lg px-4 py-2.5 text-xs font-semibold transition ${
            activeTab === "assigned"
              ? "bg-ink text-white"
              : "border border-rule bg-white text-ink-2 hover:bg-slate-50"
          }`}
        >
          Assigned to me
        </button>

        <button
          onClick={() => setActiveTab("everything")}
          className={`rounded-lg px-4 py-2.5 text-xs font-semibold transition ${
            activeTab === "everything"
              ? "bg-ink text-white"
              : "border border-rule bg-white text-ink-2 hover:bg-slate-50"
          }`}
        >
          Everything pending
        </button>

      </div>


      {/* ERROR */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <div className="font-semibold">
            Unable to load review queue
          </div>

          <div className="mt-1 text-xs">
            {error}
          </div>
        </div>
      )}


      {/* QUEUE */}
      <div className="overflow-hidden rounded-xl border border-rule bg-white shadow-sm">

        {loading ? (
          <div className="flex min-h-[350px] items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-ink-3">
              <RefreshCw
                size={18}
                className="animate-spin"
              />

              Loading review queue...
            </div>
          </div>
        ) : visibleQueue.length === 0 ? (

          <div className="flex min-h-[350px] flex-col items-center justify-center px-6 text-center">

            <div className="grid h-14 w-14 place-items-center rounded-full border border-rule bg-slate-50">
              <Inbox
                size={24}
                className="text-ink-3"
              />
            </div>

            <h3 className="mt-4 text-sm font-bold">
              {activeTab === "unassigned"
                ? "No unassigned cases"
                : activeTab === "assigned"
                ? "No cases assigned to you"
                : "Queue is clear"}
            </h3>

            <p className="mt-2 max-w-md text-xs leading-5 text-ink-2">
              {activeTab === "unassigned"
                ? "Cases requiring human review will appear here automatically after AI validation."
                : activeTab === "assigned"
                ? "Cases assigned to your reviewer account will appear here."
                : "There are currently no pending human-review cases."}
            </p>

          </div>

        ) : (

          <div>

            {/* TABLE HEADER */}
            <div className="hidden grid-cols-[1.5fr_1.4fr_.7fr_.7fr_1fr_.8fr] gap-4 border-b border-rule bg-slate-50 px-5 py-3 text-[10px] font-semibold uppercase tracking-[.12em] text-ink-3 lg:grid">

              <div>Case</div>
              <div>Diagnosis / Therapy</div>
              <div>Priority</div>
              <div>Severity</div>
              <div>Status</div>
              <div></div>

            </div>


            {/* ROWS */}
            {visibleQueue.map((item, index) => {

              const priority = getPriority(item);
              const severity = getSeverity(item);
              const styles = priorityStyles(priority);
              const status = getStatus(item);

              const id =
                item?.id ||
                item?.request_id ||
                item?.case_id;

              const caseNumber =
                item?.case_number ||
                item?.case_id ||
                item?.request_number ||
                `Case ${index + 1}`;

              const diagnosis =
                item?.diagnosis ||
                item?.diagnosis_name ||
                item?.condition ||
                "Clinical review required";

              const procedure =
                item?.procedure ||
                item?.procedure_name ||
                item?.therapy ||
                "Procedure information available";

              return (
                <button
                  key={id || index}
                  onClick={() => {
                    if (id) {
                      navigate(`/hospital/requests/${id}`);
                    }
                  }}
                  className="group grid w-full grid-cols-1 gap-4 border-b border-rule px-5 py-5 text-left transition hover:bg-slate-50 lg:grid-cols-[1.5fr_1.4fr_.7fr_.7fr_1fr_.8fr] lg:items-center"
                >

                  {/* CASE */}
                  <div>
                    <div className="text-xs font-bold text-provider">
                      {caseNumber}
                    </div>

                    <div className="mt-1 text-[11px] text-ink-3">
                      {formatDate(
                        item?.created_at ||
                        item?.submitted_at ||
                        item?.createdAt
                      )}
                    </div>
                  </div>


                  {/* DIAGNOSIS */}
                  <div>
                    <div className="text-sm font-semibold text-ink">
                      {diagnosis}
                    </div>

                    <div className="mt-1 text-xs text-ink-3">
                      {procedure}
                    </div>
                  </div>


                  {/* PRIORITY */}
                  <div>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold ${styles.badge}`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${styles.dot}`}
                      />

                      {priority}
                    </span>
                  </div>


                  {/* SEVERITY */}
                  <div>
                    <div className={`text-sm font-bold ${styles.text}`}>
                      {severity}%
                    </div>

                    <div className="mt-1 text-[10px] text-ink-3">
                      severity
                    </div>
                  </div>


                  {/* STATUS */}
                  <div>
                    <span className="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold text-amber-700">
                      {status === "PENDING"
                        ? "PENDING REVIEW"
                        : status}
                    </span>
                  </div>


                  {/* ACTION */}
                  <div className="flex items-center justify-end gap-2 text-xs font-semibold text-provider">
                    Review

                    <ChevronRight
                      size={16}
                      className="transition-transform group-hover:translate-x-1"
                    />
                  </div>

                </button>
              );
            })}

          </div>
        )}

      </div>
    </div>
  );
}