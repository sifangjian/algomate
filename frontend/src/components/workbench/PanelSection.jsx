import styles from './PanelSection.module.css'

export default function PanelSection({ number, title, path, children }) {
    const parts = title ? title.split(' — ') : []
    const key = parts[0] || ''
    const description = parts[1] || ''

    return (
        <section className={styles.panelSection}>
            <div className={styles.sectionNumber}>#{number}</div>
            <div className={styles.panelHeader}>
                {key && <span className={styles.panelKey}>[{key}]</span>}
                {description && <h2 className={styles.panelTitle}>{description}</h2>}
                {path && <span className={styles.panelPath}>{path}</span>}
            </div>
            <div className={styles.panelBody}>
                {children}
            </div>
        </section>
    )
}
