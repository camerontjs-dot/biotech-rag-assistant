/*
 * Client-side port of the Biotech RAG Assistant deterministic retrieval path.
 * Mirrors the Python core (tokenize -> BM25Okapi -> score_floor -> deterministic
 * tie-break -> ADR-012 coverage relevance gate -> extractive answer). Runs in the
 * browser (static GitHub Pages demo) and under node (parity test). No backend.
 *
 * Faithful to rank-bm25 BM25Okapi defaults: k1=1.5, b=0.75, epsilon=0.25.
 * The corpus chunks are status-gated (Approved/Effective only) at export time,
 * exactly as Python chunk_documents() does, so Draft/Obsolete never appear here.
 */
(function (global) {
  "use strict";

  var STOPWORDS = new Set(
    ("a an the of for to and or in on is are was were be been being this that these those " +
      "what which who whom how when where why do does did we you they it its our your their " +
      "with without within into onto from by as at if then than so such not no can could should " +
      "would will may might must have has had i me my them he she his her him us about over under")
      .split(/\s+/)
  );

  function tokenize(text) {
    var m = String(text).toLowerCase().match(/\w+/g);
    return m || [];
  }

  function contentTerms(text) {
    var s = new Set();
    tokenize(text).forEach(function (t) {
      if (!STOPWORDS.has(t) && t.length > 1) s.add(t);
    });
    return s;
  }

  function coverage(queryText, chunkText) {
    var q = contentTerms(queryText);
    if (q.size === 0) return 0.0;
    var c = new Set(tokenize(chunkText));
    var hit = 0;
    q.forEach(function (t) { if (c.has(t)) hit += 1; });
    return hit / q.size;
  }

  // Faithful BM25Okapi (rank-bm25 defaults).
  function BM25(docsTokens, k1, b, epsilon) {
    this.k1 = k1 == null ? 1.5 : k1;
    this.b = b == null ? 0.75 : b;
    this.epsilon = epsilon == null ? 0.25 : epsilon;
    this.N = docsTokens.length;
    this.docFreqs = [];
    this.docLen = [];
    var nd = Object.create(null);
    var totalLen = 0;
    for (var i = 0; i < this.N; i++) {
      var tokens = docsTokens[i];
      this.docLen.push(tokens.length);
      totalLen += tokens.length;
      var freq = Object.create(null);
      for (var j = 0; j < tokens.length; j++) {
        var w = tokens[j];
        freq[w] = (freq[w] || 0) + 1;
      }
      this.docFreqs.push(freq);
      for (var word in freq) nd[word] = (nd[word] || 0) + 1;
    }
    this.avgdl = this.N ? totalLen / this.N : 0;
    this._calcIdf(nd);
  }

  BM25.prototype._calcIdf = function (nd) {
    this.idf = Object.create(null);
    var idfSum = 0;
    var negatives = [];
    var count = 0;
    for (var word in nd) {
      var freq = nd[word];
      var idf = Math.log(this.N - freq + 0.5) - Math.log(freq + 0.5);
      this.idf[word] = idf;
      idfSum += idf;
      count += 1;
      if (idf < 0) negatives.push(word);
    }
    this.averageIdf = count ? idfSum / count : 0;
    var eps = this.epsilon * this.averageIdf;
    for (var n = 0; n < negatives.length; n++) this.idf[negatives[n]] = eps;
  };

  BM25.prototype.getScores = function (queryTokens) {
    var scores = new Array(this.N).fill(0);
    for (var t = 0; t < queryTokens.length; t++) {
      var q = queryTokens[t];
      var idf = this.idf[q] || 0;
      if (idf === 0) continue;
      for (var i = 0; i < this.N; i++) {
        var f = this.docFreqs[i][q] || 0;
        if (f === 0) continue;
        var denom = f + this.k1 * (1 - this.b + (this.b * this.docLen[i]) / this.avgdl);
        scores[i] += idf * ((f * (this.k1 + 1)) / denom);
      }
    }
    return scores;
  };

  // engine over the exported corpus data; returns the same shape the UI/API renders.
  // The string indexed/gated for a chunk: section heading + verbatim span. Mirrors the Python
  // retrieval.index_text() (ADR-016) so JS BM25 and the coverage gate stay byte-identical to the
  // core even though chunk.text is now the exact cited source span (heading lives in its field).
  function indexText(c) { return c.section_heading + "\n" + c.text; }

  function makeEngine(data) {
    var chunks = data.chunks;
    var bm25 = new BM25(chunks.map(function (c) { return tokenize(indexText(c)); }));
    var minTopCoverage = data.min_top_coverage == null ? 0.6 : data.min_top_coverage;
    var scoreFloor = data.score_floor == null ? 0.0 : data.score_floor;

    function query(queryText, topK) {
      topK = topK || 3;
      var qTokens = tokenize(queryText);
      if (qTokens.length === 0) return [];
      var scores = bm25.getScores(qTokens);
      var order = chunks.map(function (_, i) { return i; });
      order.sort(function (a, b) {
        if (scores[a] !== scores[b]) return scores[b] - scores[a];        // -score
        if (chunks[a].doc_id !== chunks[b].doc_id) return chunks[a].doc_id < chunks[b].doc_id ? -1 : 1;
        if (chunks[a].chunk_index !== chunks[b].chunk_index) return chunks[a].chunk_index - chunks[b].chunk_index;
        return chunks[a].chunk_id < chunks[b].chunk_id ? -1 : 1;
      });
      var hits = [];
      for (var k = 0; k < order.length; k++) {
        var idx = order[k];
        if (scores[idx] <= scoreFloor) continue;
        hits.push({ rank: hits.length + 1, score: scores[idx], chunk: chunks[idx] });
        if (hits.length >= topK) break;
      }
      // ADR-012 relevance gate on the rank-1 hit.
      if (hits.length && minTopCoverage > 0.0) {
        if (coverage(queryText, indexText(hits[0].chunk)) < minTopCoverage) return [];
      }
      return hits;
    }

    function answer(queryText, topK) {
      var hits = query(queryText, topK);
      if (!hits.length) {
        return { outcome: "refusal", answer_text: data.refusal_text, hits: [],
                 review_recommended: true, reasons: ["refusal_no_supporting_documents"],
                 documents_excluded: data.documents_excluded, documents_retrievable: data.documents_retrievable };
      }
      return { outcome: "answer", answer_text: null,
               hits: hits.map(function (h) { return { score: h.score, chunk: h.chunk }; }),
               citations_valid: true, review_recommended: false, reasons: [],
               documents_excluded: data.documents_excluded, documents_retrievable: data.documents_retrievable };
    }

    return { query: query, answer: answer, bm25: bm25 };
  }

  var api = { tokenize: tokenize, contentTerms: contentTerms, coverage: coverage, BM25: BM25, makeEngine: makeEngine };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else global.BiotechRAG = api;
})(typeof window !== "undefined" ? window : globalThis);
