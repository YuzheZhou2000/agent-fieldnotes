import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import MarkdownIt from 'markdown-it';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const escape = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const fill = (template, values) => template.replace(/{{(\w+)}}/g, (_, key) => {
  if (!(key in values)) throw new Error(`Missing template value: ${key}`);
  return values[key];
});
const posts = fs.readdirSync(path.join(root, 'content')).filter(f => f.endsWith('.md')).sort().map(file => {
  const match = read(`content/${file}`).match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) throw new Error(`Invalid JSON frontmatter: ${file}`);
  const meta = JSON.parse(match[1]);
  for (const key of ['slug', 'title', 'topic', 'summary', 'order', 'updated', 'tags', 'minutes']) {
    if (!(key in meta)) throw new Error(`Missing ${key}: ${file}`);
  }
  if (!/^[a-z0-9-]+$/.test(meta.slug)) throw new Error(`Invalid slug: ${file}`);
  return {...meta, body: match[2], file};
}).sort((a,b) => a.order - b.order);
if (new Set(posts.map(p => p.slug)).size !== posts.length) throw new Error('Duplicate slug');
const topics = [
  {name: '运行时与状态', text: '循环、事件日志、检查点与故障恢复', slug: 'agent-loop'},
  {name: '记忆与上下文', text: '工作集、文件记忆、检索与策略训练', slug: 'context-retrieval'},
  {name: '工具与协议', text: '能力发现、调度、MCP 与 A2A', slug: 'gemini'},
  {name: '权限与安全', text: '身份、凭据、行动范围与来源传播', slug: 'muse'},
  {name: '评测与交付', text: '协作、产物验收、可靠性与完整成本', slug: 'agent-evaluation'}
];
if (posts.some(p => !topics.some(t => t.name === p.topic))) throw new Error('Unknown topic');
const legacyIds = JSON.parse(read('templates/heading-ids.json'));
const thumbs = JSON.parse(read('templates/thumbnails.json'));
const tags = p => p.tags.map(t => `<span class="tag">${escape(t)}</span>`).join('');
const output = new Map();
for (let i = 0; i < posts.length; i++) {
  const post = posts[i];
  const md = new MarkdownIt({html: true});
  const headings = [];
  const used = new Set(['sources', ...Object.values(legacyIds[post.slug] || {})]);
  md.renderer.rules.heading_open = (tokens, index) => {
    const raw = tokens[index + 1].content;
    const title = md.utils.unescapeAll(md.renderInline(raw).replace(/<[^>]*>/g, ''));
    let id = legacyIds[post.slug]?.[title];
    if (!id) {
      const base = `h-${createHash('sha256').update(title).digest('hex').slice(0,12)}`;
      id = base;
      for (let n = 2; used.has(id); n++) id = `${base}-${n}`;
    } else if (headings.some(h => h.id === id)) {
      throw new Error(`Duplicate legacy heading: ${post.slug}/${id}`);
    }
    used.add(id);
    headings.push({id, title, level: Number(tokens[index].tag.slice(1))});
    return `<${tokens[index].tag} id="${id}">`;
  };
  let body = md.render(post.body).replace(/<table>/g, '<div class="table-wrap"><table>').replace(/<\/table>/g, '</table></div>');
  body = body.replace(/<a href="(https?:[^"]+)"/g, '<a href="$1" target="_blank" rel="noopener noreferrer"');
  let toc = '<ul>\n';
  let nested = false;
  for (const h of headings) {
    if (h.level === 2) {
      if (nested) { toc += '</ul></li>\n'; nested = false; }
      else if (toc !== '<ul>\n') toc += '</li>\n';
      toc += `<li><a href="#${h.id}">${escape(h.title)}</a>`;
    } else {
      if (!nested) { toc += '<ul>\n'; nested = true; }
      toc += `<li><a href="#${h.id}">${escape(h.title)}</a></li>\n`;
    }
  }
  toc += nested ? '</ul></li>\n' : '</li>\n';
  toc += '<li><a href="#sources">来源与证据说明</a></li>\n</ul>';
  if (post.collapsibleToc) {
    toc = '<details><summary>展开章节与题目目录</summary>' + toc + '</details>';
  }
  const next = posts[(i + 1) % posts.length];
  const split = post.title.indexOf('：');
  const titleLines = split < 0 ? escape(post.title) : `<span class="title-line">${escape(post.title.slice(0,split+1))}</span><span class="title-line">${escape(post.title.slice(split+1))}</span>`;
  output.set(`posts/${post.slug}.html`, fill(read('templates/post.html'), {
    ...Object.fromEntries(Object.entries(post).map(([k,v]) => [k, escape(v)])),
    number: String(post.order).padStart(2,'0'), description: escape(post.summary), titleLines,
    tags: tags(post), toc, body, nextSlug: next.slug, nextTitle: escape(next.title)
  }));
}
const card = p => `<a class="card" href="posts/${p.slug}.html" data-topic="${escape(p.topic)}" data-slug="${p.slug}">
<div class="thumb"><span class="card-number">${String(p.order).padStart(2,'0')}</span><span class="learned-badge" hidden>已学习 ✓</span>${thumbs[p.slug] || thumbs['agent-memory']}</div>
<div class="card-body"><div class="card-meta">${escape(p.topic)}<span>约 ${p.minutes} 分钟</span></div><h3>${escape(p.title)}</h3><p>${escape(p.summary)}</p><div class="tag-row">${tags(p)}</div><div class="card-footer"><time datetime="${p.updated}">${p.updated}</time><span class="arrow">→</span></div></div></a>`;
const displayPosts = [...posts].sort((a,b) => Number(b.order >= 7) - Number(a.order >= 7) || a.order - b.order);
output.set('index.html', fill(read('templates/index.html'), {
  count: posts.length, updated: posts.map(p => p.updated).sort().at(-1), cards: displayPosts.map(card).join('\n'),
  filters: ['all', ...topics.map(t=>t.name)].map((t,i) => `<button type="button" data-filter="${escape(t)}" aria-pressed="${i===0}">${t==='all'?'全部':escape(t)}</button>`).join(''),
  directions: topics.map((t,i)=>`<a class="direction-card" href="posts/${t.slug}.html" data-choose-topic="${escape(t.name)}"><span class="mono">0${i+1}</span><h3>${escape(t.name)}</h3><p>${escape(t.text)}</p><small>${posts.filter(p=>p.topic===t.name).length} 篇笔记 →</small></a>`).join('\n')
}));
output.set('assets/search-index.js', `window.FIELDNOTES_SEARCH = ${JSON.stringify(posts.map(p=>({slug:p.slug,text:[p.title,p.summary,p.topic,...p.tags,p.body].join(' ').toLowerCase()})))};\n`);
const route = JSON.parse(read('content/learning-path.json'));
const knownPosts = new Map(posts.map(p => [p.slug, p]));
if (!/^\d{4}-\d{2}-\d{2}$/.test(route.updated) || new Set(route.stages.map(s => s.id)).size !== route.stages.length) throw new Error('Invalid learning route metadata');
for (const stage of route.stages) {
  if (!/^[a-z-]+$/.test(stage.id) || !['available', 'planned'].includes(stage.coverage) || !stage.title || !stage.kind || !stage.question || !stage.outcome || !stage.exercise || !stage.next) throw new Error('Invalid learning route stage');
  if (stage.posts.some(slug => !knownPosts.has(slug)) || (stage.coverage === 'available') !== (stage.posts.length > 0)) throw new Error(`Invalid route readings: ${stage.id}`);
}
output.set('learn.html', fill(read('templates/learn.html'), {
  count: posts.length, updated: route.updated,
  available: route.stages.filter(s => s.coverage === 'available').length,
  planned: route.stages.filter(s => s.coverage === 'planned').length,
  jumps: route.stages.map((s,i) => `<a href="#${s.id}">${i+1}. ${escape(s.title)}</a>`).join('\n'),
  stages: route.stages.map((s,i) => `<section id="${s.id}" class="route-stage" data-coverage="${s.coverage}"><span class="route-number" aria-hidden="true">${String(i+1).padStart(2,'0')}</span><div><span class="coverage-label">${escape(s.kind)}</span><h2>${escape(s.title)}</h2><p><strong>${escape(s.question)}</strong></p><p>${escape(s.outcome)}</p>${s.posts.length ? '<ul>'+s.posts.map(slug=>`<li><a href="posts/${slug}.html">${escape(knownPosts.get(slug).title)}</a></li>`).join('')+'</ul>' : '<p>暂无独立专题，以下是准备方向。</p>'}<p><strong>练习：</strong>${escape(s.exercise)}</p><p class="route-next">${escape(s.next)}</p></div></section>`).join('\n')
}));
output.set('tools/loop-lab.html', fill(read('templates/loop-lab.html'), {updated: route.updated}));
const check = process.argv.includes('--check');
const stale = [];
for (const [file, contents] of output) {
  if (check) { if (!fs.existsSync(path.join(root,file)) || read(file) !== contents) stale.push(file); }
  else { fs.mkdirSync(path.dirname(path.join(root,file)), {recursive: true}); fs.writeFileSync(path.join(root,file), contents); }
}
if (stale.length) throw new Error(`Generated files are stale; run npm run build:\n${stale.join('\n')}`);
console.log(`${check ? 'Checked' : 'Built'} ${posts.length} posts, ${topics.length} technical directions, homepage and offline search.`);
