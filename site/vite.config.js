import { readFileSync } from 'node:fs';
import { Marked } from 'marked';

const esc = (text) => text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const md = new Marked({
  renderer: {
    // The page owns h1 to h3, so a saved "# Title" becomes h4 and deeper levels follow.
    heading({ tokens, depth }) { const h = `h${Math.min(6, depth + 3)}`; return `<${h}>${this.parser.parseInline(tokens)}</${h}>`; },
    // Saved text is shown, never run: raw HTML prints as text and an image prints as its alt text.
    html: ({ text }) => esc(text),
    image: ({ text }) => esc(text),
  },
});
// tabindex: a long text scrolls inside its box, so the keyboard must be able to reach it.
const body = (name, text) => name.endsWith('.md')
  ? `<div class="md" tabindex="0">${md.parse(text)}</div>`
  : `<pre class="md" tabindex="0">${esc(text)}</pre>`;
const doc = (cls, label, text, questions) =>
  `<figure class="${cls}"><figcaption>${label}</figcaption>${body('.md', text)}${
    questions ? `<p class="tag">Saved beside it: open-questions.md</p>${body('.md', questions)}` : ''}</figure>`;

// Fills every <div class="pair" data-case> with the full saved texts, at build time, so the page reads with scripting off.
export default {
  plugins: [{
    name: 'saved-runs',
    transformIndexHtml(html) {
      const cases = JSON.parse(readFileSync(new URL('cases.json', import.meta.url), 'utf8'));
      return html.replace(/<div class="pair" data-case="([^"]+)" data-run="[^"]+"><\/div>/g, (_, id) => {
        const c = cases[id];
        if (!c) throw new Error(`cases.json has no ${id}; run node collect-cases.mjs`);
        const sources = Object.entries(c.files).map(([name, text]) =>
          `<details class="given"><summary>Given: ${esc(name)}</summary>${body(name, text.trim())}</details>`).join('');
        const same = c.without === c.with ? '<p class="trace">The two saved texts are identical.</p>' : '';
        return `${sources}<div class="pair">${doc('without', 'Without the skill', c.without, c.withoutQuestions)}${doc('output', 'With the skill', c.with, c.withQuestions)}</div>${same}`;
      });
    },
  }],
};
