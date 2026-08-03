// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'IntelliStream DataHub',
  tagline: 'A shared model of your operation',
  favicon: 'img/favicon.ico',

  // This site publishes at https://intellistream.ai/data-platform-documentation.
  // /documentation is already taken by a marketing page on the main site, and the
  // SDK docs move alongside these to /sdk-documentation.
  // baseUrl matters: every generated asset and route is prefixed with it, so
  // the production web server must serve the build under /data-platform-documentation/.
  url: 'https://intellistream.ai',
  baseUrl: '/data-platform-documentation/',
  organizationName: 'intellistream',
  projectName: 'datahub-docs',
  onBrokenLinks: 'warn',
  markdown: {
    mermaid: true,
    hooks: { onBrokenMarkdownLinks: 'warn' },
  },

  i18n: { defaultLocale: 'en', locales: ['en'] },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: '/',          // docs at site root, GitBook-style
          // Adds "Edit this page" to every doc. Docusaurus appends the file's
          // path relative to this site directory, so this points at the repo
          // root on the default branch — main here, master in datahub-sdk-docs.
          editUrl: 'https://github.com/IntelliStream-DataHub/datahub-docs/edit/main/',
        },
        blog: false,
        theme: { customCss: './src/css/custom.css' },
      }),
    ],
  ],

  themes: [
    '@docusaurus/theme-mermaid',
    [
      '@easyops-cn/docusaurus-search-local',
      /** @type {import('@easyops-cn/docusaurus-search-local').PluginOptions} */
      ({
        hashed: true,
        indexDocs: true,
        indexBlog: false,
        docsRouteBasePath: '/',
        highlightSearchTermsOnTargetPage: true,
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: { respectPrefersColorScheme: true },
      mermaid: {
        theme: { light: 'neutral', dark: 'dark' },
        options: {
          // Diagrams are rendered into a full-width container (see custom.css),
          // so bump the base font rather than letting mermaid size for a small canvas.
          fontSize: 16,
          flowchart: { useMaxWidth: false, nodeSpacing: 55, rankSpacing: 65, padding: 14 },
          themeVariables: {
            primaryColor: '#eaf2f6',
            primaryBorderColor: '#005984',
            primaryTextColor: '#1d2b36',
            lineColor: '#6b8995',
            fontFamily: 'Manrope, Helvetica, Arial, sans-serif',
            fontSize: '16px',
          },
        },
      },
      navbar: {
        title: 'DataHub',
        // '/' is the main site root, not this site's baseUrl. That only works
        // because src/theme/Logo is ejected to pass href through verbatim —
        // stock Docusaurus would rewrite this to /data-platform-documentation/.
        logo: {
          alt: 'IntelliStream',
          src: 'img/logo.svg',
          srcDark: 'img/logo-dark.svg',
          href: '/',
          target: '_self',
        },
        items: [
          { type: 'docSidebar', sidebarId: 'docsSidebar', position: 'left', label: 'Documentation' },
          { to: '/start/what-is-datahub', label: 'Start here', position: 'left' },
          { to: '/value/business-case', label: 'Business value', position: 'left' },
          { to: '/administration/overview', label: 'Administration', position: 'left' },
          // Absolute, not root-relative: Docusaurus prefixes a leading-slash href
          // with this site's baseUrl, which would point it back inside these docs.
          { href: 'https://intellistream.ai/sdk-documentation/', label: 'Developer & SDK docs', position: 'right' },
          { href: 'https://www.intellistream.ai', label: 'intellistream.ai', position: 'right' },
          { href: 'https://github.com/IntelliStream-DataHub/datahub-docs', label: 'GitHub', position: 'right' },
        ],
      },
      footer: {
        style: 'light',
        links: [
          {
            title: 'Start here',
            items: [
              { label: 'What DataHub is', to: '/start/what-is-datahub' },
              { label: 'What is Industry 4.0?', to: '/start/industry-4' },
              { label: 'The four building blocks', to: '/start/core-ideas' },
              { label: 'Your first hour', to: '/start/first-hour' },
              { label: 'Glossary', to: '/reference/glossary' },
            ],
          },
          {
            title: 'Understand the model',
            items: [
              { label: 'What is an ontology?', to: '/concepts/ontology' },
              { label: 'Taxonomy vs. ontology', to: '/concepts/taxonomy' },
              { label: 'Knowledge graphs', to: '/concepts/knowledge-graph' },
              { label: 'Contextualization', to: '/concepts/contextualization' },
              { label: 'Naming standards', to: '/concepts/naming-and-standards' },
            ],
          },
          {
            title: 'For leadership',
            items: [
              { label: 'The business case', to: '/value/business-case' },
              { label: 'The cost of doing nothing', to: '/value/cost-of-doing-nothing' },
              { label: 'Where to start', to: '/value/where-to-start' },
              { label: 'AI agents', to: '/value/ai-agents' },
              { label: 'Board briefing', to: '/value/board-briefing' },
            ],
          },
          {
            title: 'More',
            items: [
              { label: 'Administration', to: '/administration/overview' },
              { label: 'Developer & SDK docs', href: 'https://intellistream.ai/sdk-documentation/' },
              { label: 'intellistream.ai', href: 'https://www.intellistream.ai' },
              { label: 'Contact us', href: 'https://intellistream.ai/contact-us' },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} IntelliStream.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['java', 'python', 'bash', 'json', 'yaml', 'sql'],
      },
    }),
};

export default config;
