import React from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';

/**
 * Shared building blocks for the DataHub user docs.
 *
 * These are registered globally in `src/theme/MDXComponents.js`, so any .mdx
 * page can use `<Cards>`, `<KeyIdea>` etc. without an import line. Styling
 * lives in `src/css/custom.css`.
 */

/** The one-minute answer at the top of a page, before any detail. */
export function KeyIdea({title = 'In one minute', children}) {
  return (
    <div className="key-idea">
      <div className="key-idea__title">{title}</div>
      <div className="key-idea__body">{children}</div>
    </div>
  );
}

/** A one-sentence framing paragraph under the page title. */
export function Lead({children}) {
  return <p className="lead">{children}</p>;
}

/** Grid wrapper for `<Card>`. Use `wide` for two roomy columns. */
export function Cards({children, wide = false}) {
  return (
    <div className={wide ? 'card-grid card-grid--two' : 'card-grid'}>{children}</div>
  );
}

/** A click-through card. `to` for internal routes, `href` for external ones. */
export function Card({title, to, href, icon, eyebrow, children}) {
  const body = (
    <>
      {icon && <div className="doc-card__icon">{icon}</div>}
      {eyebrow && <div className="doc-card__eyebrow">{eyebrow}</div>}
      <div className="doc-card__title">{title}</div>
      <div className="doc-card__body">{children}</div>
    </>
  );
  return (
    <Link className="doc-card" to={to} href={href}>
      {body}
    </Link>
  );
}

/**
 * Marks a capability that is planned rather than shipped.
 *
 * Documenting a roadmap feature is fine; letting a reader mistake it for
 * something they can use today is not. Every page describing unshipped
 * behaviour opens with one of these.
 */
export function Roadmap({title = 'On the roadmap', children}) {
  return (
    <div className="roadmap">
      <div className="roadmap__title">{title}</div>
      <div className="roadmap__body">{children}</div>
    </div>
  );
}

/** External sources for a topic, so a reader can check us against neutral ground. */
export function References({title = 'External references', children}) {
  return (
    <div className="references">
      <div className="references__title">{title}</div>
      {children}
    </div>
  );
}

/** A "go deeper" list for readers who want the detail behind a simple page. */
export function Deeper({title = 'Go deeper', children}) {
  return (
    <div className="deeper">
      <div className="deeper__title">{title}</div>
      {children}
    </div>
  );
}

/** Chips naming who a page is written for. */
export function Personas({children}) {
  return <div className="persona-row">{children}</div>;
}

/** One persona chip. `primary` highlights the main audience. */
export function Persona({children, primary = false}) {
  return <span className={primary ? 'persona persona--lead' : 'persona'}>{children}</span>;
}

/** Grid wrapper for `<Stat>`. */
export function Stats({children}) {
  return <div className="stat-grid">{children}</div>;
}

/** A single headline figure with a label and an optional caveat. */
export function Stat({value, label, note}) {
  return (
    <div className="stat">
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
      {note && <div className="stat__note">{note}</div>}
    </div>
  );
}

/**
 * A framed diagram. The brand SVGs are drawn for a light background, so the
 * frame stays light in dark mode too — see `.figure` in custom.css.
 */
export function Figure({src, alt, caption, wide = false, children}) {
  // Two modes. `src` loads a self-contained SVG with <img> — simple, but the
  // file cannot see the page theme, so it sits in an always-light frame.
  // `children` takes an inlined SVG (imported via SVGR), which page CSS can
  // reach, so it follows the theme toggle and gets a themed frame.
  const themed = !src && children;
  // Site-rooted asset paths must carry the baseUrl (/documentation/) in
  // production. Markdown links get this automatically; raw <img> src does not.
  const resolvedSrc = useBaseUrl(src ?? '');
  const cls = [
    'figure',
    themed ? 'figure--themed' : '',
    wide ? 'figure--wide' : '',
  ].filter(Boolean).join(' ');
  return (
    <figure className={cls}>
      {themed ? children : <img src={resolvedSrc} alt={alt} />}
      {caption && <figcaption className="figure__caption">{caption}</figcaption>}
    </figure>
  );
}

/** Grid of labelled brand glyphs. */
export function IconRow({children}) {
  return <div className="icon-row">{children}</div>;
}

/** One glyph with a label and an optional note. */
export function IconItem({src, label, note}) {
  const resolvedSrc = useBaseUrl(src);
  return (
    <div className="icon-item">
      <img src={resolvedSrc} alt="" />
      <div className="icon-item__label">{label}</div>
      {note && <div className="icon-item__note">{note}</div>}
    </div>
  );
}

/** Numbered walkthrough. Wrap `<Step>` children. */
export function Steps({children}) {
  return <div className="steps">{children}</div>;
}

/** One step in a `<Steps>` walkthrough. */
export function Step({title, children}) {
  return (
    <div className="step">
      {title && <div className="step__title">{title}</div>}
      <div className="step__body">{children}</div>
    </div>
  );
}
