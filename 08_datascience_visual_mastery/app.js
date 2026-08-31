(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const labels = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0];
  const scores = [0.95, 0.83, 0.62, 0.36, 0.79, 0.55, 0.41, 0.18, 0.09, 0.02];

  const esc = (value) => String(value).replace(/[&<>]/g, (mark) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;'
  }[mark]));

  function addFeatureControls() {
    const controls = document.querySelector('#bayes .controls');
    if (!controls || $('feature2Pos')) return;
    const note = controls.querySelector('.control-note');
    const html = `
      <div class="control"><label for="feature2Pos">P(feature 2 | class) <output id="feature2PosOut">0.70</output></label>
        <input id="feature2Pos" type="range" min="0" max="1" step="0.01" value="0.70"></div>
      <div class="control"><label for="feature2Neg">P(feature 2 | not class) <output id="feature2NegOut">0.30</output></label>
        <input id="feature2Neg" type="range" min="0" max="1" step="0.01" value="0.30"></div>`;
    note.insertAdjacentHTML('beforebegin', html);
    $('prior').min = '0';
    $('prior').max = '1';
    $('likePos').min = '0';
    $('likeNeg').min = '0';
    $('likePos').previousElementSibling.firstChild.textContent = 'P(feature 1 | class) ';
    $('likeNeg').previousElementSibling.firstChild.textContent = 'P(feature 1 | not class) ';
    ['prior', 'likePos', 'likeNeg', 'feature2Pos', 'feature2Neg'].forEach((id) => $(id).addEventListener('input', updateBayes));
  }

  function formatRatio(value, suffix = '') {
    return value == null ? `undefined${suffix}` : `${(value * 100).toFixed(0)}%${suffix}`;
  }

  function bayesPosterior(prior, positive, negative) {
    const positiveProduct = positive.reduce((product, value) => product * value, 1);
    const negativeProduct = negative.reduce((product, value) => product * value, 1);
    const denominator = positiveProduct * prior + negativeProduct * (1 - prior);
    return denominator === 0 ? null : positiveProduct * prior / denominator;
  }

  function bar(x, y, width, height, value, color, label, sublabel) {
    const shownHeight = Math.max(4, height * (value || 0));
    const shownValue = value == null ? 'undefined' : value.toFixed(2);
    return `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="12" fill="#edf0f6"/>` +
      (value == null ? '' : `<rect x="${x}" y="${y + height - shownHeight}" width="${width}" height="${shownHeight}" rx="12" fill="${color}"/>`) +
      `<text x="${x + width / 2}" y="${y + height + 24}" text-anchor="middle" fill="#71809a" font-size="13" font-weight="700">${label}</text>` +
      `<text x="${x + width / 2}" y="${value == null ? y + height / 2 : y + height - shownHeight - 10}" text-anchor="middle" fill="#182238" font-weight="800" font-size="18">${shownValue}</text>` +
      `<text x="${x + width / 2}" y="${y + height + 41}" text-anchor="middle" fill="#a0aabd" font-size="11">${sublabel}</text>`;
  }

  function updateBayes() {
    const prior = +$('prior').value;
    const feature1Positive = +$('likePos').value;
    const feature1Negative = +$('likeNeg').value;
    const feature2Positive = +$('feature2Pos').value;
    const feature2Negative = +$('feature2Neg').value;
    const posterior = bayesPosterior(prior, [feature1Positive, feature2Positive], [feature1Negative, feature2Negative]);
    $('priorOut').textContent = prior.toFixed(2);
    $('likePosOut').textContent = feature1Positive.toFixed(2);
    $('likeNegOut').textContent = feature1Negative.toFixed(2);
    $('feature2PosOut').textContent = feature2Positive.toFixed(2);
    $('feature2NegOut').textContent = feature2Negative.toFixed(2);
    $('bayesSvg').innerHTML = `<text x="34" y="31" fill="#34415c" font-size="16" font-weight="800">Two conditionally independent features update belief</text>` +
      `<line x1="328" y1="145" x2="465" y2="145" stroke="#7d5cf5" stroke-width="3" stroke-linecap="round"/>` +
      `<path d="M452 137 L468 145 L452 153" fill="none" stroke="#7d5cf5" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>` +
      bar(125, 57, 150, 158, prior, '#aab6cb', 'prior', 'before evidence') +
      bar(510, 57, 150, 158, posterior, '#3b6cf5', 'posterior', 'after feature 1 + 2');
    const evidenceText = posterior == null
      ? 'The evidence has zero probability under both classes, so the posterior is undefined.'
      : `Feature likelihood products are ${(feature1Positive * feature2Positive).toFixed(3)} vs ${(feature1Negative * feature2Negative).toFixed(3)}. Belief moves from ${(prior * 100).toFixed(0)}% to ${(posterior * 100).toFixed(0)}%; the base rate still matters.`;
    $('bayesNote').textContent = evidenceText;
  }

  function confusionAt(threshold) {
    let tp = 0; let fp = 0; let tn = 0; let fn = 0;
    labels.forEach((actual, index) => {
      const predicted = scores[index] >= threshold ? 1 : 0;
      if (actual === 1 && predicted === 1) tp += 1;
      else if (actual === 0 && predicted === 1) fp += 1;
      else if (actual === 0) tn += 1;
      else fn += 1;
    });
    return {
      tp, fp, tn, fn,
      precision: tp + fp ? tp / (tp + fp) : null,
      recall: tp + fn ? tp / (tp + fn) : null,
      fpr: fp + tn ? fp / (fp + tn) : null
    };
  }

  function rocPoints() {
    const points = [[0, 0]];
    [...new Set(scores)].sort((a, b) => b - a).forEach((threshold) => {
      const metrics = confusionAt(threshold);
      points.push([metrics.fpr || 0, metrics.recall || 0]);
    });
    points.push([1, 1]);
    return points.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  }

  function auc(points) {
    return points.slice(1).reduce((total, point, index) => {
      const previous = points[index];
      return total + (point[0] - previous[0]) * (point[1] + previous[1]) / 2;
    }, 0);
  }

  function matrixSvg(metrics, x, y, title, showCosts = false) {
    const cells = [
      ['TP', metrics.tp, '0', '#e8f8f5'], ['FN', metrics.fn, '4', '#fff2e8'],
      ['FP', metrics.fp, '1', '#fff2e8'], ['TN', metrics.tn, '0', '#e8f8f5']
    ];
    const labels = showCosts ? cells.map(([name, count, cost]) => `${name}: ${count} · cost ${cost}`) : cells.map(([name, count]) => `${name}: ${count}`);
    return `<rect x="${x}" y="${y}" width="310" height="${showCosts ? 152 : 162}" rx="14" fill="#f7f9ff" stroke="#e2e7f1"/>` +
      `<text x="${x + 155}" y="${y + 25}" text-anchor="middle" fill="#34415c" font-weight="800" font-size="14">${title}</text>` +
      `<text x="${x + 106}" y="${y + 50}" text-anchor="middle" fill="#71809a" font-size="12">pred +</text><text x="${x + 230}" y="${y + 50}" text-anchor="middle" fill="#71809a" font-size="12">pred −</text>` +
      `<text x="${x + 13}" y="${y + 78}" fill="#71809a" font-size="12">actual +</text><text x="${x + 13}" y="${y + 126}" fill="#71809a" font-size="12">actual −</text>` +
      cells.map((cell, index) => {
        const cx = x + (index % 2 ? 178 : 55); const cy = y + (index < 2 ? 57 : 105);
        return `<rect x="${cx}" y="${cy}" width="62" height="40" rx="8" fill="${cell[3]}"/><text x="${cx + 31}" y="${cy + 16}" text-anchor="middle" fill="#172033" font-size="11" font-weight="800">${labels[index]}</text><text x="${cx + 31}" y="${cy + 33}" text-anchor="middle" fill="#71809a" font-size="10">${showCosts ? 'count × cost' : 'count'}</text>`;
      }).join('');
  }

  function updateEval() {
    const threshold = +$('threshold').value;
    const metrics = confusionAt(threshold);
    const points = rocPoints();
    const area = auc(points);
    [['tp', metrics.tp], ['fp', metrics.fp], ['tn', metrics.tn], ['fn', metrics.fn]].forEach(([key, value]) => $(key).textContent = value);
    $('thresholdOut').textContent = threshold.toFixed(2);
    $('evalNote').textContent = `Precision ${formatRatio(metrics.precision)} · recall ${formatRatio(metrics.recall)} · false-positive rate ${formatRatio(metrics.fpr)} · ROC-AUC ${area.toFixed(3)} · cost ${metrics.fp}×1 + ${metrics.fn}×4 = ${metrics.fp + 4 * metrics.fn} units.`;
    const originX = 463; const originY = 270; const width = 280; const height = 180;
    const pointPath = points.map(([fpr, tpr]) => `${originX + fpr * width},${originY - tpr * height}`).join(' ');
    const currentX = originX + (metrics.fpr || 0) * width;
    const currentY = originY - (metrics.recall || 0) * height;
    const ticks = [0, 0.5, 1].map((tick) => `<text x="${originX + tick * width}" y="${originY + 22}" text-anchor="middle" fill="#71809a" font-size="11">${tick}</text><text x="${originX - 14}" y="${originY - tick * height + 4}" text-anchor="end" fill="#71809a" font-size="11">${tick}</text>`).join('');
    const roc = `<line x1="${originX}" y1="${originY}" x2="${originX + width}" y2="${originY - height}" stroke="#e1e6f0" stroke-dasharray="7 7" stroke-width="2"/><polyline points="${pointPath}" fill="none" stroke="#7d5cf5" stroke-width="4" stroke-linejoin="round"/><circle cx="${currentX}" cy="${currentY}" r="9" fill="#d95d9b" stroke="#fff" stroke-width="4"/><text x="${originX + width / 2}" y="${originY + 53}" text-anchor="middle" fill="#71809a" font-size="12">false-positive rate</text><text x="${originX - 42}" y="${originY - height / 2}" transform="rotate(-90 ${originX - 42} ${originY - height / 2})" text-anchor="middle" fill="#71809a" font-size="12">true-positive rate</text>${ticks}<text x="${originX + width / 2}" y="52" text-anchor="middle" fill="#34415c" font-weight="800" font-size="14">ROC curve · AUC ${area.toFixed(3)}</text><text x="${currentX}" y="${currentY - 14}" text-anchor="middle" fill="#d95d9b" font-size="11" font-weight="800">current cutoff</text>`;
    $('evalSvg').setAttribute('viewBox', '0 0 800 390');
    $('evalSvg').innerHTML = matrixSvg(metrics, 48, 48, 'Confusion matrix') + matrixSvg(metrics, 48, 224, 'Cost matrix · actual × predicted', true) + roc;
  }

  function updateCalc() {
    const x = +$('xPoint').value; const rate = +$('rate').value;
    const slope = 2 * (x - 3); const path = [x];
    for (let index = 0; index < 6; index += 1) path.push(path[path.length - 1] - rate * 2 * (path[path.length - 1] - 3));
    $('xOut').textContent = x.toFixed(2); $('rateOut').textContent = rate.toFixed(2);
    const xMin = -2.5; const xMax = 7.5; const yMin = 0; const yMax = 34;
    const gx = (value) => 90 + (value - xMin) * 66; const gy = (value) => 302 - (value - yMin) / (yMax - yMin) * 232;
    const curve = Array.from({ length: 101 }, (_, index) => `L${gx(xMin + index * 0.1)} ${gy((xMin + index * 0.1 - 3) ** 2 + 1)}`).join(' ');
    const points = path.map((value) => `${gx(value)},${gy((value - 3) ** 2 + 1)}`).join(' ');
    const tangentStart = Math.max(xMin, x - 2); const tangentEnd = Math.min(xMax, x + 2);
    const tangent = (value) => (x - 3) ** 2 + 1 + slope * (value - x);
    $('calcSvg').setAttribute('viewBox', '0 0 800 350');
    $('calcSvg').innerHTML = `<text x="34" y="31" fill="#34415c" font-size="16" font-weight="800">The tangent tells you which way to step</text><line x1="75" y1="302" x2="755" y2="302" stroke="#aeb8cc"/><path d="M${gx(xMin)} ${gy((xMin - 3) ** 2 + 1)} ${curve}" fill="none" stroke="#1fa08e" stroke-width="4" stroke-linecap="round"/><line x1="${gx(tangentStart)}" y1="${gy(tangent(tangentStart))}" x2="${gx(tangentEnd)}" y2="${gy(tangent(tangentEnd))}" stroke="#f58b45" stroke-width="3" stroke-linecap="round"/><polyline points="${points}" fill="none" stroke="#3b6cf5" stroke-width="3" stroke-linecap="round" stroke-dasharray="4 5"/>${path.map((value, index) => `<circle cx="${gx(value)}" cy="${gy((value - 3) ** 2 + 1)}" r="${index === 0 ? 9 : 5}" fill="${index === 0 ? '#f58b45' : '#3b6cf5'}" stroke="#fff" stroke-width="3"/>`).join('')}<text x="${gx(x) + 14}" y="${gy((x - 3) ** 2 + 1) - 13}" fill="#c66a2e" font-size="12" font-weight="800">slope ${slope.toFixed(2)}</text><text x="${gx(3)}" y="334" text-anchor="middle" fill="#71809a" font-size="12">minimum · x = 3</text>`;
    $('calcNote').textContent = `At x=${x.toFixed(1)}, the slope is ${slope.toFixed(2)} and loss is ${((x - 3) ** 2 + 1).toFixed(2)}. The blue points apply x ← x − η·slope.`;
  }

  function updateBp() {
    const w = +$('weight').value; const b = +$('bias').value; const x = 2; const target = 10;
    const y = w * x + b; const error = y - target; const loss = 0.5 * error ** 2; const dW = error * x; const dB = error;
    $('weightOut').textContent = w.toFixed(2); $('biasOut').textContent = b.toFixed(2);
    const nodes = [['x = 2', 90, 90], [`w = ${w.toFixed(1)}`, 90, 205], ['w×x', 280, 148], [`b = ${b.toFixed(1)}`, 390, 245], ['+ b', 470, 148], [`ŷ = ${y.toFixed(1)}`, 610, 148], [`L = ${loss.toFixed(1)}`, 740, 148]];
    const nodeSvg = nodes.map(([label, xPos, yPos]) => `<circle cx="${xPos}" cy="${yPos}" r="34" fill="#eef2ff" stroke="#3b6cf5" stroke-width="2"/><text x="${xPos}" y="${yPos + 5}" text-anchor="middle" fill="#182238" font-weight="800" font-size="13">${esc(label)}</text>`).join('');
    const lines = [[124, 90, 246, 135], [124, 205, 246, 160], [314, 148, 436, 148], [424, 245, 452, 177], [504, 148, 576, 148], [644, 148, 706, 148]];
    const lineSvg = lines.map(([x1, y1, x2, y2]) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#3b6cf5" stroke-width="3" marker-end="url(#arrow)"/>`).join('');
    $('bpSvg').setAttribute('viewBox', '0 0 800 340');
    $('bpSvg').innerHTML = `<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#3b6cf5"/></marker></defs><text x="34" y="31" fill="#34415c" font-size="16" font-weight="800">Forward values go right. Gradients come back.</text>${lineSvg}${nodeSvg}<text x="400" y="69" text-anchor="middle" fill="#3b6cf5" font-size="12" font-weight="800">forward pass →</text><text x="400" y="285" text-anchor="middle" fill="#d95d9b" font-size="12" font-weight="800">← backward · dL/dŷ = ${error.toFixed(1)} · dL/dw = ${dW.toFixed(1)} · dL/db = ${dB.toFixed(1)}</text><text x="400" y="315" text-anchor="middle" fill="#71809a" font-size="11">local factors: dŷ/d(w×x) = 1 · d(w×x)/dw = x = 2 · dŷ/db = 1</text>`;
    $('bpNote').textContent = `One affine neuron: prediction ${y.toFixed(1)} versus target ${target}; error ${error.toFixed(1)}. The bias receives dL/db = dL/dŷ because ∂ŷ/∂b = 1.`;
  }

  function updateCopyAndLabels() {
    const bayesMath = document.querySelector('#bayes .math');
    if (bayesMath) bayesMath.innerHTML = 'P(C | E₁, E₂) = <strong>P(E₁ | C)P(E₂ | C)P(C)</strong> / P(E₁, E₂)<span>Naive Bayes multiplies conditionally independent feature likelihoods, then normalizes</span>';
    const evalMath = document.querySelector('#evaluation .math');
    if (evalMath) evalMath.innerHTML = 'precision = TP/(TP+FP) &nbsp; · &nbsp; recall = TP/(TP+FN) &nbsp; · &nbsp; FPR = FP/(FP+TN)<span>ROC-AUC summarizes ranking across thresholds; a cost matrix assigns a cost to each outcome cell</span>';
    const backpropCopy = document.querySelector('#backprop .copy-card p');
    if (backpropCopy) backpropCopy.textContent = 'This one-neuron affine model computes a prediction forward, then multiplies local derivatives backward. The same chain rule scales to hidden layers; this visual keeps the graph small enough to audit.';
    const backpropMath = document.querySelector('#backprop .math');
    if (backpropMath) backpropMath.innerHTML = 'ŷ = wx + b &nbsp; · &nbsp; L = ½(ŷ − y)²<br>∂L/∂w = (∂L/∂ŷ)(∂ŷ/∂w) &nbsp; · &nbsp; ∂L/∂b = (∂L/∂ŷ)(1)<span>the chain rule turns one output error into two parameter gradients</span>';
    const backpropHeader = document.querySelector('#backprop .lesson-header p');
    if (backpropHeader) backpropHeader.textContent = 'Trace error backward through one affine neuron.';
    const backpropPrompt = document.querySelector('#backprop .prompt-card p');
    if (backpropPrompt) backpropPrompt.textContent = 'Adjust the weight and bias. The graph makes the multiplication and addition explicit, then shows how the loss gradient branches back to both parameters.';
    const evalPrompt = document.querySelector('#evaluation .simulation-top p');
    if (evalPrompt) evalPrompt.textContent = 'Move the cutoff and see the matrix, cost cells, ROC curve, and current point move.';
    const evalSvg = document.getElementById('evalSvg');
    if (evalSvg) evalSvg.setAttribute('aria-label', 'Confusion matrix, cost matrix, and ROC curve with AUC');
  }

  function wireNavigation() {
    const lessons = ['bayes', 'evaluation', 'calculus', 'backprop'];
    const status = ['Start with evidence', 'Compare the consequences', 'Follow the slope', 'Trace the credit'];
    const showLesson = (id) => {
      const index = lessons.indexOf(id); if (index < 0) return;
      document.querySelectorAll('.lesson').forEach((section) => section.classList.toggle('active', section.id === id));
      document.querySelectorAll('[data-tab]').forEach((button) => button.setAttribute('aria-current', button.dataset.tab === id ? 'page' : 'false'));
      $('progressRing').textContent = `${index + 1}/4`; $('railStatus').textContent = status[index];
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    document.querySelectorAll('[data-tab]').forEach((button) => button.addEventListener('click', () => showLesson(button.dataset.tab)));
    document.querySelectorAll('.next-lesson').forEach((button) => button.addEventListener('click', () => showLesson(button.dataset.next)));
    document.querySelectorAll('.check').forEach((button) => button.addEventListener('click', () => {
      const card = button.closest('.quiz'); const selected = card.querySelector('input:checked'); const feedback = card.querySelector('.feedback');
      if (!selected) { feedback.textContent = 'Choose an answer first.'; feedback.style.color = '#c66a2e'; return; }
      const correct = selected.value === card.dataset.answer;
      feedback.textContent = correct ? 'Correct — nice reasoning.' : 'Not quite. Re-read the visual and try again.';
      feedback.style.color = correct ? '#1f8e7d' : '#c14e77';
    }));
  }

  addFeatureControls();
  updateCopyAndLabels();
  wireNavigation();
  ['threshold'].forEach((id) => $(id).addEventListener('input', updateEval));
  ['xPoint', 'rate'].forEach((id) => $(id).addEventListener('input', updateCalc));
  ['weight', 'bias'].forEach((id) => $(id).addEventListener('input', updateBp));
  updateBayes(); updateEval(); updateCalc(); updateBp();
})();
