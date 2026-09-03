import { useEffect, useMemo, useState } from "react";
import "./App.css";

/* ========================================================= */
/* CONFIG */
/* ========================================================= */

const API_BASE_URL = "http://127.0.0.1:8000";

const HISTORY_KEY = "tark_execution_history";

const MAX_HISTORY_ITEMS = 50;


/* ========================================================= */
/* PIPELINE */
/* ========================================================= */

const PIPELINE_STEPS = [
  {
    number: "01",
    key: "MARKET",
    title: "MARKET",
    subtitle: "Quant Features",
  },
  {
    number: "02",
    key: "OPPORTUNITY",
    title: "OPPORTUNITY",
    subtitle: "Signal Detection",
  },
  {
    number: "03",
    key: "THESIS",
    title: "THESIS",
    subtitle: "AI Reasoning",
  },
  {
    number: "04",
    key: "FRAGILITY",
    title: "FRAGILITY",
    subtitle: "Structural Risk",
  },
  {
    number: "05",
    key: "CONTRACTS",
    title: "CONTRACTS",
    subtitle: "Options Selection",
  },
  {
    number: "06",
    key: "RISK",
    title: "RISK",
    subtitle: "Capital Protection",
  },
  {
    number: "07",
    key: "EXECUTION",
    title: "EXECUTION",
    subtitle: "Order Control",
  },
];


/* ========================================================= */
/* HELPERS */
/* ========================================================= */

function isNonEmptyObject(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.keys(value).length > 0
  );
}


function normalizeStage(stage) {
  if (!stage) return "";

  const value = String(stage)
    .trim()
    .toUpperCase()
    .replace(/[-\s]+/g, "_");

  const stageMap = {
    MARKET: "MARKET",
    DATA: "MARKET",
    FEATURES: "MARKET",

    OPPORTUNITY: "OPPORTUNITY",
    SIGNAL: "OPPORTUNITY",

    THESIS: "THESIS",
    AI_THESIS: "THESIS",

    FRAGILITY: "FRAGILITY",

    CONTRACTS: "CONTRACTS",
    CONTRACT_SELECTION: "CONTRACTS",
    OPTIONS: "CONTRACTS",

    RISK: "RISK",
    RISK_GOVERNANCE: "RISK",
    RISK_GOVERNOR: "RISK",

    EXECUTION: "EXECUTION",

    AUTONOMOUS_SCAN: "MARKET",
    SCAN: "MARKET",
  };

  return stageMap[value] || value;
}


function getStageIndex(stage) {
  const normalized = normalizeStage(stage);

  return PIPELINE_STEPS.findIndex(
    (item) => item.key === normalized
  );
}


function formatCurrency(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "--";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return "$" + String(value);
  }

  return new Intl.NumberFormat(
    "en-US",
    {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }
  ).format(number);
}


function formatNumber(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "--";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return String(value);
  }

  return new Intl.NumberFormat(
    "en-US",
    {
      maximumFractionDigits: 2,
    }
  ).format(number);
}


function formatPercent(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "--";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return String(value);
  }

  return formatNumber(number) + "%";
}


/* ========================================================= */
/* RESPONSE NORMALIZATION */
/* ========================================================= */

function normalizeResponse(responseData) {
  if (!responseData) {
    return {
      mode: "MANUAL",
      symbol: "--",
      selectedSymbol: "--",
      result: null,
      scanSummary: null,
      raw: null,
    };
  }

  const result =
    responseData.result ||
    responseData.decision ||
    null;

  const autonomous =
    responseData.mode === "AUTONOMOUS" ||
    !!responseData.selected_symbol ||
    !!responseData.scan_summary;

  const symbol =
    responseData.symbol ||
    result?.symbol ||
    responseData.selected_symbol ||
    "--";

  const selectedSymbol =
    responseData.selected_symbol ||
    result?.symbol ||
    responseData.symbol ||
    "--";

  return {
    mode: autonomous ? "AUTONOMOUS" : "MANUAL",

    symbol,

    selectedSymbol,

    result,

    scanSummary:
      responseData.scan_summary ||
      responseData.autonomous_data?.scan_summary ||
      null,

    raw: responseData,
  };
}


function getResultStatus(result, data) {
  return (
    result?.status ||
    data?.status ||
    "UNKNOWN"
  );
}


function getExecutionStatus(result) {
  if (!result) {
    return "NOT RUN";
  }

  const status = String(
    result.status || ""
  ).toUpperCase();

  if (status === "WAIT") {
    return "NOT EXECUTED";
  }

  if (status === "ABSTAIN") {
    return "ABSTAINED";
  }

  if (status === "BLOCKED") {
    return "BLOCKED";
  }

  return (
    result.execution?.status ||
    result.status ||
    "NOT EXECUTED"
  );
}


function formatHistoryTime(timestamp) {
  if (!timestamp) {
    return "--";
  }

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  return date.toLocaleString(
    undefined,
    {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}


/* ========================================================= */
/* APP */
/* ========================================================= */

function App() {

  /* ======================================================= */
  /* STATE */
  /* ======================================================= */

  const [symbol, setSymbol] = useState("QQQ");

  const [data, setData] = useState(null);

  const [loading, setLoading] = useState(false);

  const [loadingMode, setLoadingMode] =
    useState(null);

  const [error, setError] = useState(null);

  const [history, setHistory] = useState([]);


  /* ======================================================= */
  /* LOAD HISTORY */
  /* ======================================================= */

  useEffect(() => {
    try {
      const savedHistory =
        localStorage.getItem(HISTORY_KEY);

      if (!savedHistory) return;

      const parsed = JSON.parse(savedHistory);

      if (Array.isArray(parsed)) {
        setHistory(parsed);
      }

    } catch (error) {
      console.error(
        "Failed to load TARK history:",
        error
      );

      localStorage.removeItem(HISTORY_KEY);
    }
  }, []);


  /* ======================================================= */
  /* SAVE HISTORY */
  /* ======================================================= */

  const saveToHistory = (responseData) => {
    try {

      const normalized =
        normalizeResponse(responseData);

      const result = normalized.result;

      const historyItem = {
        id:
          responseData?.registry_id
            ? "registry-" + responseData.registry_id
            : Date.now() +
              "-" +
              Math.random()
                .toString(36)
                .substring(2, 8),

        registryId:
          responseData?.registry_id || null,

        timestamp:
          new Date().toISOString(),

        mode:
          normalized.mode,

        symbol:
          normalized.selectedSymbol ||
          normalized.symbol ||
          "--",

        status:
          getResultStatus(
            result,
            responseData
          ),

        stage:
          result?.stage ||
          responseData?.stage ||
          "--",

        strategy:
          result?.opportunity?.strategy ||
          "--",

        direction:
          result?.opportunity?.direction ||
          "--",

        fragility:
          result?.fragility?.score ??
          "--",

        approvedContracts:
          result?.risk?.approved_contracts ??
          "--",

        message:
          result?.message ||
          responseData?.message ||
          "--",

        data: responseData,
      };


      setHistory((previousHistory) => {

        const withoutDuplicate =
          historyItem.registryId
            ? previousHistory.filter(
                (item) =>
                  item.registryId !==
                  historyItem.registryId
              )
            : previousHistory;

        const updatedHistory = [
          historyItem,
          ...withoutDuplicate,
        ].slice(
          0,
          MAX_HISTORY_ITEMS
        );

        localStorage.setItem(
          HISTORY_KEY,
          JSON.stringify(updatedHistory)
        );

        return updatedHistory;
      });

    } catch (error) {
      console.error(
        "Failed to save TARK history:",
        error
      );
    }
  };


  /* ======================================================= */
  /* MANUAL ANALYSIS */
  /* ======================================================= */

  const analyzeSymbol = async () => {

    const cleanSymbol =
      symbol.trim().toUpperCase();

    if (!cleanSymbol) {
      setError(
        "Please enter a market symbol."
      );
      return;
    }

    try {

      setLoading(true);
      setLoadingMode("MANUAL");
      setError(null);
      setData(null);

      const response =
        await fetch(
          API_BASE_URL +
          "/analyze/" +
          cleanSymbol
        );

      const responseData =
        await response.json();

      if (!response.ok) {
        throw new Error(
          responseData?.detail?.message ||
          responseData?.detail?.error ||
          responseData?.detail ||
          "TARK analysis failed"
        );
      }

      setData(responseData);

      saveToHistory(responseData);

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Unable to analyze symbol."
      );

      setData(null);

    } finally {

      setLoading(false);
      setLoadingMode(null);

    }
  };


  /* ======================================================= */
  /* AUTONOMOUS SCAN */
  /* ======================================================= */

  const autonomousScan = async () => {

    try {

      setLoading(true);
      setLoadingMode("AUTONOMOUS");
      setError(null);
      setData(null);

      const response =
        await fetch(
          API_BASE_URL + "/autonomous"
        );

      const responseData =
        await response.json();

      if (!response.ok) {
        throw new Error(
          responseData?.detail?.message ||
          responseData?.detail?.error ||
          responseData?.detail ||
          "Autonomous TARK execution failed"
        );
      }

      setData(responseData);

      saveToHistory(responseData);

    } catch (error) {

      console.error(error);

      setError(
        error.message ||
        "Autonomous scan failed."
      );

      setData(null);

    } finally {

      setLoading(false);
      setLoadingMode(null);

    }
  };


  /* ======================================================= */
  /* HISTORY */
  /* ======================================================= */

  const loadHistoryItem = (item) => {

    if (!item?.data) return;

    setData(item.data);

    setError(null);

    if (
      item.symbol &&
      item.symbol !== "--"
    ) {
      setSymbol(item.symbol);
    }

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };


  const clearHistory = () => {

    setHistory([]);

    localStorage.removeItem(
      HISTORY_KEY
    );
  };


  /* ======================================================= */
  /* NORMALIZED DATA */
  /* ======================================================= */

  const normalized = useMemo(
    () => normalizeResponse(data),
    [data]
  );

  const autonomousMode =
    normalized.mode === "AUTONOMOUS";

  const result =
    normalized.result;


  /* ======================================================= */
  /* RESULT SECTIONS */
  /* ======================================================= */

  const opportunity =
    isNonEmptyObject(result?.opportunity)
      ? result.opportunity
      : null;

  const thesis =
    isNonEmptyObject(result?.thesis)
      ? result.thesis
      : null;

  const fragility =
    isNonEmptyObject(result?.fragility)
      ? result.fragility
      : null;

  const contracts =
    isNonEmptyObject(result?.contracts)
      ? result.contracts
      : null;

  const pricing =
    isNonEmptyObject(result?.pricing)
      ? result.pricing
      : null;

  const risk =
    isNonEmptyObject(result?.risk)
      ? result.risk
      : null;

  const execution =
    isNonEmptyObject(result?.execution)
      ? result.execution
      : null;

  const pnl =
    isNonEmptyObject(result?.pnl)
      ? result.pnl
      : isNonEmptyObject(result?.profit_loss)
        ? result.profit_loss
        : null;


  /* ======================================================= */
  /* STATUS */
  /* ======================================================= */

  const status =
    getResultStatus(result, data);

  const stage =
    normalizeStage(
      result?.stage ||
      data?.stage
    );

  const stageIndex =
    getStageIndex(stage);

  const direction =
    opportunity?.direction ||
    "NEUTRAL";

  const executionStatus =
    getExecutionStatus(result);

  const approvedContracts =
    risk?.approved_contracts ??
    "--";

  const fragilityScore =
    fragility?.score ??
    "--";

  const fragilityDecision =
    fragility?.decision ??
    "--";


  /* ======================================================= */
  /* PIPELINE STATE */
  /* ======================================================= */

  const hasMarket = !!data;

  const hasOpportunity =
    !!opportunity ||
    stageIndex >= 1;

  const hasThesis =
    !!thesis ||
    stageIndex >= 2;

  const hasFragility =
    !!fragility ||
    stageIndex >= 3;

  const hasContracts =
    !!contracts ||
    stageIndex >= 4;

  const hasRisk =
    !!risk ||
    stageIndex >= 5;

  const hasExecution =
    !!execution ||
    stageIndex >= 6;


  /* ======================================================= */
  /* AUTONOMOUS DATA */
  /* ======================================================= */

  const selectedSymbol =
    normalized.selectedSymbol;

  const scanSummary =
    normalized.scanSummary || {};

  const scannedCount =
    scanSummary.scanned_count ??
    data?.scanned_count ??
    "--";

  const candidateCount =
    scanSummary.candidate_count ??
    data?.candidate_count ??
    data?.candidates_found ??
    "--";


  /* ======================================================= */
  /* P&L DATA */
  /* ======================================================= */

  const unrealizedPnl =
    pnl?.unrealized_pnl ??
    pnl?.unrealized ??
    pnl?.current_pnl ??
    "--";

  const realizedPnl =
    pnl?.realized_pnl ??
    pnl?.realized ??
    "--";

  const totalPnl =
    pnl?.total_pnl ??
    pnl?.net_pnl ??
    pnl?.pnl ??
    "--";

  const pnlPercent =
    pnl?.pnl_percent ??
    pnl?.return_percent ??
    pnl?.return_pct ??
    "--";

  const entryValue =
    pnl?.entry_value ??
    pnl?.cost_basis ??
    pricing?.estimated_debit ??
    "--";

  const currentValue =
    pnl?.current_value ??
    pnl?.market_value ??
    "--";


  /* ======================================================= */
  /* RENDER */
  /* ======================================================= */

  return (

    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div>

          <h1>TARK</h1>

          <p>
            <span>THINK FIRST.</span>
            <span> RISK SECOND.</span>
          </p>

        </div>

        <div className="system-status">
          ● SYSTEM ONLINE
        </div>

      </header>


      {/* HERO */}

      <section className="hero">

        <div className="hero-content">

          <div className="eyebrow">
            AUTONOMOUS OPTIONS INTELLIGENCE
          </div>

          <h2>
            Reason Before Risk.
          </h2>

          <p>
            TARK evaluates market structure,
            trading opportunity, AI reasoning,
            structural fragility, options
            selection, risk governance, and
            execution before capital is deployed.
          </p>


          <div className="symbol-controls">

            <div className="symbol-input">

              <label>
                MARKET SYMBOL
              </label>

              <input
                value={symbol}
                disabled={loading}
                onChange={(event) =>
                  setSymbol(
                    event.target.value.toUpperCase()
                  )
                }
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !loading
                  ) {
                    analyzeSymbol();
                  }
                }}
                placeholder="QQQ"
              />

            </div>


            <div className="action-buttons">

              <button
                className="analyze-button"
                onClick={analyzeSymbol}
                disabled={loading}
              >

                {
                  loading &&
                  loadingMode === "MANUAL"
                    ? "ANALYZING..."
                    : "ANALYZE SYMBOL"
                }

              </button>


              <button
                className="autonomous-button"
                onClick={autonomousScan}
                disabled={loading}
              >

                {
                  loading &&
                  loadingMode === "AUTONOMOUS"
                    ? "SCANNING..."
                    : "AUTONOMOUS SCAN"
                }

              </button>

            </div>

          </div>


          {loading && (

            <div className="loading-status">

              <div className="loading-indicator">
                ●
              </div>

              {
                loadingMode === "AUTONOMOUS"
                  ? "TARK is scanning the configured market universe and evaluating candidates..."
                  : "TARK is running the complete decision pipeline..."
              }

            </div>

          )}


          {error && (

            <div className="error">
              {error}
            </div>

          )}

        </div>

      </section>


      {/* DASHBOARD */}

      <main className="dashboard">


        {/* AUTONOMOUS SUMMARY */}

        {autonomousMode && (

          <section className="autonomous-summary">

            <div>

              <div className="section-label">
                AUTONOMOUS MARKET SCAN
              </div>

              <h3>

                {
                  selectedSymbol &&
                  selectedSymbol !== "--"
                    ? (
                      <>
                        TARK SELECTED{" "}
                        <strong>
                          {selectedSymbol}
                        </strong>
                      </>
                    )
                    : "NO TRADE CANDIDATE SELECTED"
                }

              </h3>

              <p>

                {
                  result?.message ||
                  data?.message ||
                  "TARK independently scanned the configured market universe and evaluated available opportunities."
                }

              </p>

            </div>


            <div className="autonomous-metrics">

              <MetricCard
                label="SYMBOLS SCANNED"
                value={scannedCount}
              />

              <MetricCard
                label="CANDIDATES FOUND"
                value={candidateCount}
              />

              <MetricCard
                label="SELECTED"
                value={selectedSymbol || "--"}
              />

            </div>

          </section>

        )}


        {/* PIPELINE STATUS */}

        {data && (

          <section
            className={
              "pipeline-status " +
              String(status)
                .toLowerCase()
                .replace(/\s+/g, "_")
            }
          >

            <div className="pipeline-status-label">

              {
                autonomousMode
                  ? "AUTONOMOUS PIPELINE STATUS"
                  : "PIPELINE STATUS"
              }

            </div>


            <div className="pipeline-status-content">

              <div>

                <strong>
                  {status}
                </strong>

                <span>
                  {stage || "--"}
                </span>

              </div>

              <p>

                {
                  result?.message ||
                  data?.message ||
                  "TARK analysis completed."
                }

              </p>

            </div>

          </section>

        )}


        {/* DECISION PIPELINE */}

        <section className="pipeline-section">

          <div className="section-label">
            AUTONOMOUS DECISION SYSTEM
          </div>

          <div className="pipeline-header">

            <div>

              <h3>
                TARK DECISION PIPELINE
              </h3>

              <p>
                Every trade passes through
                deterministic intelligence
                and risk gates before execution.
              </p>

            </div>

          </div>


          <div className="pipeline">

            <PipelineStep
              {...PIPELINE_STEPS[0]}
              active={hasMarket}
              current={stage === "MARKET"}
            />

            <PipelineConnector
              active={hasOpportunity}
            />

            <PipelineStep
              {...PIPELINE_STEPS[1]}
              active={hasOpportunity}
              current={stage === "OPPORTUNITY"}
            />

            <PipelineConnector
              active={hasThesis}
            />

            <PipelineStep
              {...PIPELINE_STEPS[2]}
              active={hasThesis}
              current={stage === "THESIS"}
            />

            <PipelineConnector
              active={hasFragility}
            />

            <PipelineStep
              {...PIPELINE_STEPS[3]}
              active={hasFragility}
              current={stage === "FRAGILITY"}
            />

            <PipelineConnector
              active={hasContracts}
            />

            <PipelineStep
              {...PIPELINE_STEPS[4]}
              active={hasContracts}
              current={stage === "CONTRACTS"}
            />

            <PipelineConnector
              active={hasRisk}
            />

            <PipelineStep
              {...PIPELINE_STEPS[5]}
              active={hasRisk}
              current={stage === "RISK"}
            />

            <PipelineConnector
              active={hasExecution}
            />

            <PipelineStep
              {...PIPELINE_STEPS[6]}
              active={hasExecution}
              current={stage === "EXECUTION"}
            />

          </div>

        </section>


        {/* MARKET DECISION */}

        <section className="section">

          <div className="section-header">

            <div>

              <div className="section-label">
                LIVE DECISION PIPELINE
              </div>

              <h3>
                MARKET DECISION
              </h3>

            </div>


            <div
              className={
                "status-badge " +
                String(direction).toLowerCase()
              }
            >
              {direction}
            </div>

          </div>


          <div className="metrics-grid">

            <MetricCard
              label="PIPELINE STATUS"
              value={status}
              subValue={stage || "--"}
            />

            <MetricCard
              label="EXECUTION STATUS"
              value={executionStatus}
              subValue={
                execution?.message ||
                "Order Control"
              }
            />

            <MetricCard
              label="FRAGILITY SCORE"
              value={
                fragilityScore !== "--"
                  ? String(fragilityScore) + " / 100"
                  : "--"
              }
              subValue={
                fragility?.classification ||
                "NOT EVALUATED"
              }
            />

            <MetricCard
              label="FRAGILITY DECISION"
              value={fragilityDecision}
              subValue="Capital Adjustment"
            />

            <MetricCard
              label="APPROVED SIZE"
              value={approvedContracts}
              subValue="Contracts"
            />

            <MetricCard
              label="STRATEGY"
              value={
                opportunity?.strategy ||
                "--"
              }
              subValue="Options Structure"
            />

          </div>

        </section>


        {/* AI THESIS */}

        <section className="section">

          <div className="section-header">

            <div>

              <div className="section-label">
                REASONING LAYER
              </div>

              <h3>
                AI THESIS
              </h3>

            </div>


            <div className="confidence">

              CONFIDENCE:{" "}

              <strong>
                {thesis?.confidence || "--"}
              </strong>

            </div>

          </div>


          <div className="thesis-grid">

            <EvidencePanel
              title="SUPPORTING EVIDENCE"
              items={
                thesis?.supporting_evidence ||
                []
              }
            />

            <EvidencePanel
              title="CONTRADICTIONS & RISK"
              items={
                thesis?.contradictions ||
                []
              }
            />

          </div>


          <div className="scenario-grid">

            <ScenarioCard
              label="NEUTRAL SCENARIO"
              value={
                thesis?.neutral_scenario ||
                "No scenario available."
              }
            />

            <ScenarioCard
              label="FAILURE SCENARIO"
              value={
                thesis?.failure_scenario ||
                "No scenario available."
              }
            />

          </div>

        </section>


        {/* FRAGILITY */}

        <section className="section">

          <div className="section-label">
            STRUCTURAL RISK ANALYSIS
          </div>

          <h3>
            FRAGILITY ENGINE
          </h3>


          <div className="fragility-layout">

            <div className="fragility-score">

              <div className="score-number">
                {fragility?.score ?? "--"}
              </div>

              <div className="score-label">
                / 100
              </div>

              <div className="classification">

                {
                  fragility?.classification ||
                  "NOT EVALUATED"
                }

              </div>

              <div className="fragility-action">

                ACTION:{" "}

                <strong>

                  {
                    fragility?.decision ||
                    "SKIPPED"
                  }

                </strong>

              </div>

            </div>


            <div className="fragility-components">

              <FragilityRow
                label="TREND"
                value={
                  fragility?.components?.trend
                }
              />

              <FragilityRow
                label="MOMENTUM"
                value={
                  fragility?.components?.momentum
                }
              />

              <FragilityRow
                label="VOLUME"
                value={
                  fragility?.components?.volume
                }
              />

              <FragilityRow
                label="NEUTRAL PRESSURE"
                value={
                  fragility?.components?.neutral_pressure
                }
              />

              <FragilityRow
                label="FAILURE PRESSURE"
                value={
                  fragility?.components?.failure_pressure
                }
              />

              <FragilityRow
                label="VOLATILITY"
                value={
                  fragility?.components?.volatility
                }
              />

            </div>

          </div>

        </section>


        {/* OPTIONS */}

        <section className="section">

          <div className="section-label">
            CONTRACT SELECTION
          </div>

          <h3>
            OPTIONS STRUCTURE
          </h3>


          <div className="options-grid">

            <OptionLeg
              title="BUY"
              leg={contracts?.long_leg}
            />

            <OptionLeg
              title="SELL"
              leg={contracts?.short_leg}
            />

            <MetricCard
              label="EXPIRATION"
              value={
                contracts?.expiration_date ||
                contracts?.expiration ||
                "--"
              }
              subValue="Selected Expiry"
            />

          </div>

        </section>


        {/* PRICING */}

        <section className="section">

          <div className="section-label">
            OPTIONS PRICING
          </div>

          <h3>
            TRADE PRICING
          </h3>


          <div className="metrics-grid">

            <MetricCard
              label="ESTIMATED DEBIT"
              value={
                formatCurrency(
                  pricing?.estimated_debit
                )
              }
            />

            <MetricCard
              label="MAX PROFIT"
              value={
                formatCurrency(
                  pricing?.max_profit
                )
              }
            />

            <MetricCard
              label="MAX LOSS"
              value={
                formatCurrency(
                  pricing?.max_loss
                )
              }
            />

            <MetricCard
              label="RISK / REWARD"
              value={
                pricing?.risk_reward ??
                "--"
              }
            />

          </div>

        </section>


        {/* P&L */}

        <section className="section pnl-section">

          <div className="section-header">

            <div>

              <div className="section-label">
                POSITION PERFORMANCE
              </div>

              <h3>
                PROFIT & LOSS
              </h3>

            </div>


            <div className="confidence">

              LIVE POSITION METRICS
            </div>

          </div>


          <div className="metrics-grid">

            <MetricCard
              label="UNREALIZED P&L"
              value={
                formatCurrency(unrealizedPnl)
              }
              subValue="Current Open Position"
            />

            <MetricCard
              label="REALIZED P&L"
              value={
                formatCurrency(realizedPnl)
              }
              subValue="Closed Position Result"
            />

            <MetricCard
              label="TOTAL P&L"
              value={
                formatCurrency(totalPnl)
              }
              subValue="Net Performance"
            />

            <MetricCard
              label="RETURN"
              value={
                pnlPercent === "--"
                  ? "--"
                  : formatPercent(pnlPercent)
              }
              subValue="Percentage Return"
            />

            <MetricCard
              label="ENTRY VALUE"
              value={
                formatCurrency(entryValue)
              }
              subValue="Initial Position Cost"
            />

            <MetricCard
              label="CURRENT VALUE"
              value={
                formatCurrency(currentValue)
              }
              subValue="Current Market Value"
            />

          </div>


          <div className="risk-status">

            POSITION STATUS:{" "}

            <strong>

              {
                pnl?.status ||
                execution?.status ||
                "NO ACTIVE POSITION"
              }

            </strong>

          </div>

        </section>


        {/* RISK */}

        <section className="section">

          <div className="section-label">
            CAPITAL PROTECTION LAYER
          </div>

          <h3>
            RISK GOVERNOR
          </h3>


          <div className="metrics-grid">

            <MetricCard
              label="MAX TRADE RISK"
              value={
                formatCurrency(
                  risk?.max_trade_risk
                )
              }
            />

            <MetricCard
              label="RISK PER SPREAD"
              value={
                formatCurrency(
                  risk?.risk_per_spread
                )
              }
            />

            <MetricCard
              label="REQUESTED"
              value={
                risk?.requested_contracts ??
                "--"
              }
              subValue="Contracts"
            />

            <MetricCard
              label="APPROVED"
              value={
                risk?.approved_contracts ??
                "--"
              }
              subValue="Contracts"
            />

            <MetricCard
              label="PROPOSED MAX LOSS"
              value={
                formatCurrency(
                  risk?.proposed_max_loss
                )
              }
            />

            <MetricCard
              label="PORTFOLIO RISK"
              value={
                formatCurrency(
                  risk?.proposed_portfolio_risk
                )
              }
            />

          </div>


          <div className="risk-status">

            RISK GOVERNOR:{" "}

            <strong>

              {
                risk?.status ||
                "NOT EVALUATED"
              }

            </strong>

          </div>

        </section>


        {/* EXECUTION */}

        <section className="section execution-section">

          <div className="section-label">
            EXECUTION LAYER
          </div>

          <h3>
            EXECUTION ENGINE
          </h3>


          <div className="execution-grid">

            <MetricCard
              label="STATUS"
              value={
                execution?.status ||
                executionStatus
              }
            />

            <MetricCard
              label="LIMIT PRICE"
              value={
                formatCurrency(
                  execution?.order?.limit_price
                )
              }
            />

            <MetricCard
              label="CONTRACTS"
              value={
                execution?.order?.contracts ??
                "--"
              }
            />

          </div>


          {execution?.message && (

            <div className="risk-status">

              EXECUTION MESSAGE:{" "}

              <strong>
                {execution.message}
              </strong>

            </div>

          )}

        </section>


        {/* HISTORY */}

        <section className="section history-section">

          <div className="section-header">

            <div>

              <div className="section-label">
                DECISION MEMORY
              </div>

              <h3>
                TARK HISTORY
              </h3>

              <p>
                Previous autonomous scans and
                symbol-level TARK decisions.
              </p>

            </div>


            {history.length > 0 && (

              <button
                className="clear-history-button"
                onClick={clearHistory}
              >
                CLEAR HISTORY
              </button>

            )}

          </div>


          {history.length === 0 ? (

            <div className="history-empty">
              No previous TARK decisions yet.
            </div>

          ) : (

            <div className="history-list">

              {history.map((item) => (

                <div
                  key={item.id}
                  className="history-item"
                  onClick={() =>
                    loadHistoryItem(item)
                  }
                >

                  <div className="history-main">

                    <div className="history-symbol">
                      {item.symbol}
                    </div>

                    <div className="history-strategy">

                      {item.mode}

                      {" • "}

                      {item.strategy}

                    </div>

                  </div>


                  <div className="history-meta">

                    <div className="history-details">

                      Fragility:{" "}

                      <strong>
                        {item.fragility}
                      </strong>

                      {" | "}

                      Approved:{" "}

                      <strong>
                        {item.approvedContracts}
                      </strong>

                    </div>


                    <div
                      className={
                        "history-status " +
                        String(
                          item.status || "unknown"
                        )
                          .toLowerCase()
                          .replace(/\s+/g, "_")
                      }
                    >
                      {item.status}
                    </div>


                    <div className="history-time">
                      {formatHistoryTime(item.timestamp)}
                    </div>

                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      </main>


      {/* FOOTER */}

      <footer className="footer">
        TARK — REASON BEFORE RISK
      </footer>

    </div>

  );
}


/* ========================================================= */
/* COMPONENTS */
/* ========================================================= */

function MetricCard({
  label,
  value,
  subValue,
}) {

  return (

    <div className="metric-card">

      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}
      </div>

      {subValue && (

        <div className="metric-subvalue">
          {subValue}
        </div>

      )}

    </div>

  );
}


function EvidencePanel({
  title,
  items = [],
}) {

  return (

    <div className="evidence-panel">

      <h4>
        {title}
      </h4>


      {
        !Array.isArray(items) ||
        items.length === 0
          ? (
            <p className="empty">
              No analysis available.
            </p>
          )
          : (
            <ul>

              {items.map(
                (item, index) => (

                  <li key={index}>
                    {String(item)}
                  </li>

                )
              )}

            </ul>
          )
      }

    </div>

  );
}


function ScenarioCard({
  label,
  value,
}) {

  return (

    <div className="scenario-card">

      <div className="metric-label">
        {label}
      </div>

      <p>
        {value}
      </p>

    </div>

  );
}


function FragilityRow({
  label,
  value,
}) {

  const safeValue =
    Number(value) || 0;

  const percentage =
    Math.min(
      Math.max(
        safeValue * 5,
        0
      ),
      100
    );

  return (

    <div className="fragility-row">

      <div className="fragility-row-header">

        <span>
          {label}
        </span>

        <span>
          {formatNumber(safeValue)}
        </span>

      </div>


      <div className="progress-track">

        <div
          className="progress-bar"
          style={{
            width:
              String(percentage) + "%",
          }}
        />

      </div>

    </div>

  );
}


function OptionLeg({
  title,
  leg,
}) {

  return (

    <div className="option-leg">

      <div className="option-title">
        {title}
      </div>

      <div className="option-symbol">
        {leg?.symbol || "--"}
      </div>

      <div className="option-details">

        <div>

          Strike:{" "}

          <strong>
            {leg?.strike ?? "--"}
          </strong>

        </div>

        <div>

          Type:{" "}

          <strong>

            {
              leg?.type ||
              leg?.option_type ||
              "--"
            }

          </strong>

        </div>

      </div>

    </div>

  );
}


function PipelineStep({
  number,
  title,
  subtitle,
  active,
  current,
}) {

  const className =
    "pipeline-step " +
    (active ? "active " : "") +
    (current ? "current" : "");

  return (

    <div className={className}>

      <div className="pipeline-number">

        {
          active && !current
            ? "✓"
            : number
        }

      </div>


      <div className="pipeline-info">

        <div className="pipeline-title">
          {title}
        </div>

        <div className="pipeline-subtitle">
          {subtitle}
        </div>

      </div>

    </div>

  );
}


function PipelineConnector({
  active = false,
}) {

  return (

    <div
      className={
        "pipeline-connector " +
        (active ? "active" : "")
      }
    />

  );
}


export default App;