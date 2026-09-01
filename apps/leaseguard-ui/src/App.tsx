// =============================================================================
// MIT License
// Copyright (c) 2026 Aparavi Software AG
// =============================================================================

/**
 * LeaseGuard AI - Enterprise Lease Audit Platform
 * RocketRide app shell integration
 *
 * This app provides the platform shell integration for LeaseGuard AI.
 * The primary UI and business logic runs on a Streamlit backend at:
 * http://localhost:8501
 *
 * This component serves as:
 * - Platform shell wrapper
 * - User context and authentication provider
 * - Navigation and status display
 * - Integration point with RocketRide services
 */

import React, { useState } from 'react';
import type { ShellAppProps } from 'shell';
import { AppLayout, Documents, DocSplitLayout, DocTabs } from 'shell';

const styles: Record<string, React.CSSProperties> = {
	wrap: {
		padding: 32,
		fontFamily: 'var(--rr-font-family, system-ui)',
		background: 'var(--rr-bg, #f7f8fb)',
		minHeight: '100%',
		color: 'var(--rr-text-primary, #121826)',
	},
	title: {
		margin: 0,
		fontSize: 28,
		fontWeight: 700,
		color: 'var(--rr-text-primary, #121826)',
	},
	sub: {
		margin: '8px 0 0',
		fontSize: 14,
		color: 'var(--rr-text-secondary, #4d5a74)',
	},
	headerRow: {
		display: 'flex',
		justifyContent: 'space-between',
		alignItems: 'center',
		gap: 16,
		marginBottom: 24,
	},
	tag: {
		display: 'inline-flex',
		alignItems: 'center',
		padding: '6px 10px',
		borderRadius: 999,
		fontSize: 12,
		fontWeight: 600,
		background: '#eaf3ff',
		color: '#214e9d',
	},
	grid: {
		display: 'grid',
		gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
		gap: 16,
		marginBottom: 24,
	},
	card: {
		background: 'var(--rr-surface, #ffffff)',
		border: '1px solid rgba(148, 163, 184, 0.25)',
		borderRadius: 16,
		padding: 18,
		boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
	},
	label: {
		fontSize: 12,
		letterSpacing: '0.04em',
		textTransform: 'uppercase',
		color: 'var(--rr-text-secondary, #4d5a74)',
		marginBottom: 8,
	},
	metric: {
		fontSize: 28,
		fontWeight: 700,
		margin: 0,
		color: 'var(--rr-text-primary, #121826)',
	},
	meta: {
		fontSize: 13,
		color: 'var(--rr-text-secondary, #4d5a74)',
		marginTop: 8,
	},
	sectionTitle: {
		margin: '0 0 12px',
		fontSize: 18,
		fontWeight: 700,
	},
	panel: {
		display: 'grid',
		gridTemplateColumns: '1.6fr 1fr',
		gap: 16,
	},
	listCard: {
		background: 'var(--rr-surface, #ffffff)',
		border: '1px solid rgba(148, 163, 184, 0.25)',
		borderRadius: 16,
		padding: 18,
	},
	leaseRow: {
		display: 'flex',
		justifyContent: 'space-between',
		alignItems: 'center',
		gap: 12,
		padding: '12px 0',
		borderBottom: '1px solid rgba(148, 163, 184, 0.2)',
	},
	leaseName: {
		fontSize: 14,
		fontWeight: 600,
		margin: 0,
	},
	leaseMeta: {
		fontSize: 12,
		color: 'var(--rr-text-secondary, #4d5a74)',
		margin: '4px 0 0',
	},
	statusPill: {
		display: 'inline-flex',
		padding: '6px 10px',
		borderRadius: 999,
		fontSize: 12,
		fontWeight: 600,
		background: '#eafaf0',
		color: '#18794e',
	},
	nav: {
		padding: '10px 8px',
		display: 'flex',
		flexDirection: 'column',
		gap: 8,
	},
	navItem: {
		padding: '8px 10px',
		borderRadius: 10,
		fontSize: 13,
		fontWeight: 600,
		color: 'var(--rr-text-primary, #121826)',
		cursor: 'pointer',
		background: 'rgba(148, 163, 184, 0.08)',
	},
	navItemActive: {
		padding: '8px 10px',
		borderRadius: 10,
		fontSize: 13,
		fontWeight: 700,
		color: '#0f172a',
		cursor: 'pointer',
		background: '#dfeaff',
	},
};

const docs = new Documents();
docs.openStaticDocument('overview', 'Quick Start');
docs.openStaticDocument('features', 'Features');
docs.openStaticDocument('api', 'API Reference');

/**
 * Portfolio metrics (demo values - connect to Streamlit backend for real data)
 */
const metrics = [
	{ label: 'Properties', value: '—', meta: 'Launch dashboard →' },
	{ label: 'Audits', value: '—', meta: 'View in Streamlit' },
	{ label: 'Findings', value: '—', meta: 'Active issues' },
	{ label: 'Recovery', value: '—', meta: 'Potential value' },
];

const leaseRows = [
	{ name: 'Dashboard', status: 'Live', detail: 'Portfolio KPIs, risk summary, recovery tracking' },
	{ name: 'Properties', status: 'Live', detail: 'Manage properties, view details and history' },
	{ name: 'Audits', status: 'Live', detail: 'Run lease audits, manual data entry, results' },
	{ name: 'Findings', status: 'Live', detail: 'Filter findings, view evidence, track status' },
	{ name: 'Risk Analysis', status: 'Live', detail: 'Portfolio risk assessment, distribution charts' },
	{ name: 'Recovery', status: 'Live', detail: 'Track recovery pipeline, status workflow' },
	{ name: 'Disputes', status: 'Live', detail: 'Generate disputes, templates, status tracking' },
	{ name: 'Analytics', status: 'Live', detail: 'Historical trends, multi-property comparison' },
	{ name: 'Documents', status: 'Live', detail: 'Upload, manage, organize lease/invoice docs' },
	{ name: 'Settings', status: 'Live', detail: 'Profile, preferences, account management' },
];

const SidebarNav: React.FC<{ activePage: string; setActivePage: (page: string) => void }> = ({
	activePage,
	setActivePage,
}) => (
	<div style={styles.nav}>
		<div
			style={activePage === 'overview' ? styles.navItemActive : styles.navItem}
			onClick={() => setActivePage('overview')}
		>
			📊 Dashboard
		</div>
		<div
			style={activePage === 'features' ? styles.navItemActive : styles.navItem}
			onClick={() => setActivePage('features')}
		>
			🏢 Pages
		</div>
		<div
			style={activePage === 'api' ? styles.navItemActive : styles.navItem}
			onClick={() => setActivePage('api')}
		>
			⚙️ Integration
		</div>
		<hr style={{ margin: '8px 0', border: '1px solid rgba(148, 163, 184, 0.2)' }} />
		<a
			href="http://localhost:8501"
			target="_blank"
			rel="noopener noreferrer"
			style={{
				...styles.navItem,
				display: 'block',
				textDecoration: 'none',
				color: '#0f172a',
			}}
		>
			→ Open Streamlit UI
		</a>
	</div>
);

const Content: React.FC<ShellAppProps & { activePage: string }> = ({
	isConnected,
	identity,
	activePage,
}) => {
	const renderContent = () => {
		if (activePage === 'features') {
			return (
				<div>
					<h2 style={styles.sectionTitle}>Phase 5 - Complete Feature Set</h2>
					<p style={styles.sub}>
						LeaseGuard AI now includes 10 fully functional pages with comprehensive analytics, audit workflows, and
						recovery tracking.
					</p>
				</div>
			);
		}

		if (activePage === 'api') {
			return (
				<div>
					<h2 style={styles.sectionTitle}>Integration & Architecture</h2>
					<p style={styles.sub}>
						<strong>Primary Interface:</strong> Streamlit app running on http://localhost:8501
					</p>
					<p style={styles.sub}>
						<strong>Backend Services:</strong> Python audit, risk, and recovery engines
					</p>
					<p style={styles.sub}>
						<strong>Data Layer:</strong> Supabase PostgreSQL with real-time sync
					</p>
					<p style={styles.sub}>
						<strong>Tech Stack:</strong> Streamlit, Plotly, Pandas, RocketRide (platform shell)
					</p>
				</div>
			);
		}

		// Default: overview
		return null;
	};

	return (
		<div style={styles.wrap}>
			<div style={styles.headerRow}>
				<div>
					<h1 style={styles.title}>LeaseGuard AI</h1>
					<p style={styles.sub}>
						Enterprise lease audit platform with AI-driven risk analysis and revenue recovery
					</p>
				</div>
				<div style={styles.tag}>
					Status: {isConnected ? '✓ Online' : '⚠ Offline'} | v1.0.0 Phase 5
				</div>
			</div>

			<div style={styles.grid}>
				{metrics.map((metric) => (
					<div key={metric.label} style={styles.card}>
						<div style={styles.label}>{metric.label}</div>
						<p style={styles.metric}>{metric.value}</p>
						<div style={styles.meta}>{metric.meta}</div>
					</div>
				))}
			</div>

			<div style={styles.panel}>
				<div style={styles.listCard}>
					<h2 style={styles.sectionTitle}>Available Pages</h2>
					{leaseRows.slice(0, 5).map((item) => (
						<div key={item.name} style={styles.leaseRow}>
							<div>
								<p style={styles.leaseName}>{item.name}</p>
								<p style={styles.leaseMeta}>{item.detail}</p>
							</div>
							<div style={styles.statusPill}>{item.status}</div>
						</div>
					))}
				</div>

				<div style={styles.listCard}>
					<h2 style={styles.sectionTitle}>Quick Links</h2>
					{leaseRows.slice(5).map((item) => (
						<div key={item.name} style={styles.leaseRow}>
							<div>
								<p style={styles.leaseName}>{item.name}</p>
								<p style={styles.leaseMeta}>{item.detail}</p>
							</div>
							<div style={styles.statusPill}>{item.status}</div>
						</div>
					))}
				</div>
			</div>

			{renderContent()}

			<div style={{ ...styles.listCard, marginTop: 24 }}>
				<h2 style={styles.sectionTitle}>User Context</h2>
				<p style={styles.sub}>
					Signed in as: <strong>{identity?.displayName ?? 'not signed in'}</strong>
				</p>
				<p style={styles.sub}>
					RocketRide connection: <strong>{isConnected ? 'connected' : 'offline'}</strong>
				</p>
				<p style={styles.sub}>
					Application mode: <strong>Production Ready</strong>
				</p>
				<p style={{ ...styles.sub, marginTop: 12 }}>
					<strong>→ Open the Streamlit dashboard</strong> to access all features: audit workflows, risk analysis,
					finding management, recovery tracking, and analytics.
				</p>
			</div>
		</div>
	);
};

const App: React.FC<ShellAppProps> = (props) => {
	const [activePage, setActivePage] = useState('overview');

	return (
		<AppLayout sidebar={<SidebarNav activePage={activePage} setActivePage={setActivePage} />} showStatus>
			<DocSplitLayout
				docs={docs}
				renderPane={(groupId) => (
					<>
						<DocTabs docs={docs} groupId={groupId} isActive />
						<Content {...props} activePage={activePage} />
					</>
				)}
			/>
		</AppLayout>
	);
};

export default App;
