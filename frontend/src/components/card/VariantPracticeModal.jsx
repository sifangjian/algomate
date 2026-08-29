import { useState, useEffect } from 'react'
import { cardService } from '../../services/cardService'
import Modal from '../ui/Modal/Modal'
import styles from './VariantPracticeModal.module.css'

export default function VariantPracticeModal({ open, problemId, problemTitle, onClose, onSaved }) {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [set, setSet] = useState(null)
  const [practiced, setPracticed] = useState({}) // slug -> bool
  const [note, setNote] = useState('')

  useEffect(() => {
    if (!open || !problemId) return
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await cardService.getVariantSet(problemId)
        if (cancelled) return
        setSet(data)
        // 默认主问题算已练（在详情页即当前题），变体题默认未勾
        const init = {}
        if (data.slug) init[data.slug] = true
        setPracticed(init)
      } catch (e) {
        if (!cancelled) setError(e.message || '加载变体题练习集失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [open, problemId])

  const toggle = (slug) => setPracticed((p) => ({ ...p, [slug]: !p[slug] }))

  const handleSave = async () => {
    const slugs = Object.keys(practiced).filter((s) => practiced[s])
    try {
      setSaving(true)
      await cardService.recordVariantPractice(problemId, { variant_slugs: slugs, note })
      onSaved?.()
      onClose?.()
    } catch (e) {
      setError(e.message || '记录练习失败')
    } finally {
      setSaving(false)
    }
  }

  const items = set ? [{ slug: set.slug, title: set.title, in_system: true, problem_id: set.problem_id, difficulty: null, solution_count: 0, leetcode_link: set.leetcode_link, isMain: true }, ...set.variants] : []

  return (
    <Modal open={open} onClose={onClose} title="变体题练习" size="lg" ariaLabel="变体题练习">
      {loading && <div className={styles.loading}>加载练习集中…</div>}
      {error && <div className={styles.error}>{error}</div>}

      {!loading && set && (
        <>
          <p className={styles.tip}>
            同考点变体题复习：把这一组题一起练，练完勾选已练的题，系统会记录本次练习轨迹。
          </p>

          <ul className={styles.list}>
            {items.map((it) => (
              <li
                key={it.slug}
                className={`${styles.item} ${it.isMain ? styles.mainItem : ''} ${practiced[it.slug] ? styles.done : ''}`}
              >
                <label className={styles.checkRow}>
                  <input
                    type="checkbox"
                    checked={!!practiced[it.slug]}
                    onChange={() => toggle(it.slug)}
                  />
                  <span className={styles.itemTitle}>
                    {it.isMain ? '★ ' : ''}{it.title || it.slug}
                  </span>
                  {it.in_system ? (
                    <span className={styles.inSys}>系统内</span>
                  ) : (
                    <span className={styles.outSys}>外部题</span>
                  )}
                  {it.difficulty && <span className={styles.diff}>{it.difficulty}</span>}
                </label>
                <a
                  className={styles.link}
                  href={it.leetcode_link || `https://leetcode.cn/problems/${it.slug}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                >
                  打开原题 ↗
                </a>
              </li>
            ))}
          </ul>

          <div className={styles.noteBox}>
            <label className={styles.noteLabel}>练习笔记</label>
            <textarea
              className={styles.noteArea}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="记录本次变体题练习的收获或易错点…"
              rows={3}
            />
          </div>

          <div className={styles.footer}>
            <span className={styles.count}>已练 {Object.values(practiced).filter(Boolean).length}/{items.length}</span>
            <div className={styles.actions}>
              <button className={styles.cancelBtn} onClick={onClose} disabled={saving}>取消</button>
              <button className={styles.saveBtn} onClick={handleSave} disabled={saving}>
                {saving ? '记录中…' : '完成练习'}
              </button>
            </div>
          </div>
        </>
      )}
    </Modal>
  )
}
