// metrics.ts — Prometheus-compatible metrics endpoint (/metrics)
//
// Lightweight implementation without external dependency (no prom-client).
// Exposes counter, gauge, histogram in Prometheus text format.
// Integrates with Express via metricsMiddleware.

const counters: Map<string, { help: string; value: number }> = new Map();
const gauges: Map<string, { help: string; value: number }> = new Map();
const histograms: Map<string, { help: string; buckets: number[]; values: number[] }> = new Map();

const DEFAULT_BUCKETS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000];

// ── registration ──

export function registerCounter(name: string, help: string) {
  counters.set(name, { help, value: 0 });
}

export function registerGauge(name: string, help: string) {
  gauges.set(name, { help, value: 0 });
}

export function registerHistogram(name: string, help: string, buckets: number[] = DEFAULT_BUCKETS) {
  histograms.set(name, { help, buckets: [...buckets], values: new Array(buckets.length + 1).fill(0) });
}

// ── mutation ──

export function incCounter(name: string, delta = 1) {
  const c = counters.get(name);
  if (c) c.value += delta;
}

export function setGauge(name: string, value: number) {
  const g = gauges.get(name);
  if (g) g.value = value;
}

export function observe(name: string, value: number) {
  const h = histograms.get(name);
  if (!h) return;
  for (let i = 0; i < h.buckets.length; i++) {
    if (value <= h.buckets[i]) {
      h.values[i]++;
      return;
    }
  }
  h.values[h.buckets.length]++; // overflow bucket
}

// ── initialization ──

registerCounter('laon_scans_total', 'Total number of scans');
registerCounter('laon_findings_critical_total', 'Critical findings detected');
registerCounter('laon_findings_high_total', 'High severity findings detected');
registerCounter('laon_findings_medium_total', 'Medium severity findings detected');
registerCounter('laon_findings_info_total', 'Info findings detected');
registerCounter('laon_llm_calls_total', 'Total LLM API calls');
registerCounter('laon_llm_tokens_total', 'Total LLM tokens consumed');
registerCounter('laon_cache_hits_total', 'Cache hits (candidates skipped)');
registerCounter('laon_errors_total', 'Total errors during scan');
registerGauge('laon_findings_open', 'Currently open (unacknowledged) findings');
registerHistogram('laon_scan_duration_ms', 'Scan duration in milliseconds');
registerHistogram('laon_llm_call_duration_ms', 'LLM call duration in milliseconds');

// ── Express middleware ──

export function metricsMiddleware(_req: unknown, res: { setHeader: (k: string, v: string) => void; end: (body: string) => void }) {
  const lines: string[] = [];

  for (const [name, { help, value }] of counters) {
    lines.push(`# HELP ${name} ${help}`);
    lines.push(`# TYPE ${name} counter`);
    lines.push(`${name} ${value}`);
  }

  for (const [name, { help, value }] of gauges) {
    lines.push(`# HELP ${name} ${help}`);
    lines.push(`# TYPE ${name} gauge`);
    lines.push(`${name} ${value}`);
  }

  for (const [name, { help, buckets, values }] of histograms) {
    lines.push(`# HELP ${name} ${help}`);
    lines.push(`# TYPE ${name} histogram`);
    for (let i = 0; i < buckets.length; i++) {
      lines.push(`${name}_bucket{le="${buckets[i]}"} ${values[i]}`);
    }
    lines.push(`${name}_bucket{le="+Inf"} ${values[buckets.length]}`);
  }

  res.setHeader('Content-Type', 'text/plain; version=0.0.4');
  res.end(lines.join('\n') + '\n');
}
