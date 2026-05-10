import { test, expect } from '@playwright/test'

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:3000'

const results = {}

test.describe('NPC Dialogue E2E Test', () => {
    test('full dialogue flow', async ({ page }) => {
        test.setTimeout(180000)

        // Step 1: Navigate to Hall page (with onboarding dismissed)
        console.log('\n=== Step 1: Navigate to Hall page ===')
        await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 })

        // Dismiss onboarding guide by setting localStorage
        await page.evaluate(() => {
            localStorage.setItem('algomate_onboarding_completed', 'true')
        })
        await page.reload({ waitUntil: 'networkidle', timeout: 30000 })
        await page.waitForTimeout(2000)

        // Also try clicking "跳过" button if onboarding still visible
        const skipBtn = page.locator('button:has-text("跳过")')
        if (await skipBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
            await skipBtn.click()
            await page.waitForTimeout(1000)
            console.log('  Dismissed onboarding guide via skip button')
        }

        console.log('  ✅ Step 1 PASS: Navigated to ' + page.url())
        results.step1 = 'PASS'

        // Step 2: Verify Hall page loads with NPC cards
        console.log('\n=== Step 2: Verify Hall page loads ===')
        const hallPageContent = await page.textContent('body')
        const hasHallTitle = hallPageContent?.includes('导师大厅') || hallPageContent?.includes('老夫子') || hallPageContent?.includes('秘境')
        console.log(`  Hall page includes NPC-related text: ${hasHallTitle}`)

        const npcCardElements = await page.locator('[role="button"]').filter({ hasText: /老夫子|墨子|鬼谷子|鲁班|华佗|诸葛亮/ }).count()
        console.log(`  NPC card elements with role=button: ${npcCardElements}`)

        const pageText = hallPageContent || ''
        const npcNames = ['老夫子', '墨子', '鬼谷子', '鲁班', '华佗', '诸葛亮']
        const foundNpc = npcNames.find(name => pageText.includes(name))
        console.log(`  Found NPC name on page: ${foundNpc || 'none'}`)

        const step2Pass = !!(hasHallTitle || foundNpc)
        results.step2 = step2Pass ? 'PASS' : 'FAIL'
        console.log(`  ${step2Pass ? '✅' : '❌'} Step 2 ${results.step2}: Hall page loaded with NPC content`)
        await page.screenshot({ path: 'e2e-results/step2-hall-page.png' })

        // Step 3: Click on an NPC card to open detail modal
        console.log('\n=== Step 3: Click NPC card to open modal ===')
        const npcCard = page.locator('[role="button"]').filter({ hasText: '老夫子' }).first()
        let npcClicked = false

        if (await npcCard.isVisible({ timeout: 5000 }).catch(() => false)) {
            await npcCard.click()
            npcClicked = true
            console.log('  Clicked 老夫子 NPC card')
        } else {
            const anyNpcCard = page.locator('[role="button"]').filter({ hasText: /老夫子|墨子|鬼谷子|鲁班|华佗|诸葛亮/ }).first()
            if (await anyNpcCard.isVisible({ timeout: 5000 }).catch(() => false)) {
                await anyNpcCard.click()
                npcClicked = true
                const cardText = await anyNpcCard.textContent().catch(() => '')
                console.log(`  Clicked NPC card: ${cardText?.substring(0, 30)}`)
            }
        }

        await page.waitForTimeout(2000)
        results.step3 = npcClicked ? 'PASS' : 'FAIL'
        console.log(`  ${npcClicked ? '✅' : '❌'} Step 3 ${results.step3}: Clicked NPC card`)
        await page.screenshot({ path: 'e2e-results/step3-npc-modal.png' })

        // Step 3.5: Click "开始修习" button in the modal to enter dialogue
        console.log('\n=== Step 3.5: Click "开始修习" in modal ===')
        const startBtn = page.locator('button:has-text("开始修习")')
        let startedDialogue = false

        if (await startBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
            await startBtn.click()
            startedDialogue = true
            console.log('  Clicked "开始修习" button')
            await page.waitForTimeout(3000)
        } else {
            console.log('  "开始修习" button not visible, may have navigated directly')
        }

        await page.screenshot({ path: 'e2e-results/step3-5-after-start.png' })
        console.log(`  Current URL: ${page.url()}`)

        // Step 4: Verify dialogue page loads
        console.log('\n=== Step 4: Verify dialogue page ===')
        const currentUrl = page.url()
        const isDialoguePage = currentUrl.includes('/npc/')
        console.log(`  Current URL: ${currentUrl}`)
        console.log(`  URL is dialogue page: ${isDialoguePage}`)

        const backButton = page.locator('button[aria-label="返回地图"], button:has-text("返回地图")')
        const hasBackButton = await backButton.isVisible({ timeout: 10000 }).catch(() => false)

        const messageInput = page.locator('textarea[aria-label="消息输入框"]')
        const hasMessageInput = await messageInput.isVisible({ timeout: 10000 }).catch(() => false)

        const sendButton = page.locator('button:has-text("发送")')
        const hasSendButton = await sendButton.isVisible({ timeout: 5000 }).catch(() => false)

        const endButton = page.locator('button:has-text("结束修习")')
        const hasEndButton = await endButton.isVisible({ timeout: 5000 }).catch(() => false)

        const chatArea = page.locator('[aria-label="对话区域"], [role="log"]')
        const hasChatArea = await chatArea.isVisible({ timeout: 5000 }).catch(() => false)

        const npcGreeting = page.locator('[class*="greeting"], [class*="npcMsg"]')
        const hasNpcGreeting = await npcGreeting.first().isVisible({ timeout: 15000 }).catch(() => false)

        console.log(`  "返回地图" button visible: ${hasBackButton}`)
        console.log(`  Message input (aria-label="消息输入框") visible: ${hasMessageInput}`)
        console.log(`  "发送" button visible: ${hasSendButton}`)
        console.log(`  "结束修习" button visible: ${hasEndButton}`)
        console.log(`  Chat area visible: ${hasChatArea}`)
        console.log(`  NPC greeting visible: ${hasNpcGreeting}`)

        const step4Pass = hasBackButton && hasMessageInput && hasSendButton && hasEndButton
        results.step4 = step4Pass ? 'PASS' : 'FAIL'
        console.log(`  ${step4Pass ? '✅' : '❌'} Step 4 ${results.step4}: Dialogue page elements check`)
        await page.screenshot({ path: 'e2e-results/step4-dialogue-page.png' })

        // Step 5: Type a message and click send
        console.log('\n=== Step 5: Type message and send ===')
        const testMessage = '什么是二分查找？'
        let messageSent = false

        if (hasMessageInput) {
            await messageInput.click()
            await page.waitForTimeout(300)
            await messageInput.fill(testMessage)
            await page.waitForTimeout(500)

            const inputValue = await messageInput.inputValue()
            console.log(`  Input value after typing: "${inputValue}"`)

            if (hasSendButton) {
                await sendButton.click()
                messageSent = true
                console.log('  Clicked "发送" button')
            } else {
                await messageInput.press('Enter')
                messageSent = true
                console.log('  Pressed Enter to send')
            }
        } else {
            console.log('  ❌ Cannot type message - input not found')
        }

        results.step5 = messageSent ? 'PASS' : 'FAIL'
        console.log(`  ${messageSent ? '✅' : '❌'} Step 5 ${results.step5}: Message sent`)
        await page.waitForTimeout(2000)
        await page.screenshot({ path: 'e2e-results/step5-after-send.png' })

        // Step 6: Verify user message appears in chat
        console.log('\n=== Step 6: Verify user message in chat ===')
        const userMsgTextEl = page.locator('[class*="msgText"]')
        const hasUserMsgTextEl = await userMsgTextEl.first().isVisible({ timeout: 5000 }).catch(() => false)

        let userMsgText = ''
        if (hasUserMsgTextEl) {
            userMsgText = await userMsgTextEl.first().textContent().catch(() => '')
            console.log(`  User message text: "${userMsgText.substring(0, 80)}"`)
        }

        const hasUserMessage = hasUserMsgTextEl && userMsgText.includes(testMessage)
        results.step6 = hasUserMessage ? 'PASS' : 'FAIL'
        console.log(`  ${hasUserMessage ? '✅' : '❌'} Step 6 ${results.step6}: User message "${testMessage}" in chat`)
        await page.screenshot({ path: 'e2e-results/step6-user-message.png' })

        // Step 7: Wait for NPC response
        console.log('\n=== Step 7: Wait for NPC response ===')
        await page.waitForTimeout(15000)

        const npcMessages = page.locator('[class*="npcMsg"]')
        const npcMsgCount = await npcMessages.count()
        console.log(`  NPC message bubbles found: ${npcMsgCount}`)

        let npcResponseText = ''
        let hasNpcResponse = false

        if (npcMsgCount >= 2) {
            npcResponseText = await npcMessages.last().textContent().catch(() => '')
            console.log(`  Last NPC message (truncated): "${npcResponseText.substring(0, 150)}..."`)
            hasNpcResponse = true
        } else if (npcMsgCount === 1) {
            npcResponseText = await npcMessages.first().textContent().catch(() => '')
            console.log(`  Only one NPC message (greeting?): "${npcResponseText.substring(0, 100)}..."`)
            hasNpcResponse = false
        } else {
            console.log('  No NPC messages found')
        }

        results.step7 = hasNpcResponse ? 'PASS' : 'WARN'
        console.log(`  ${hasNpcResponse ? '✅' : '⚠️'} Step 7 ${results.step7}: NPC response in chat`)
        await page.screenshot({ path: 'e2e-results/step7-npc-response.png' })

        // Step 8: Check 修炼日记 section
        console.log('\n=== Step 8: Check 修炼日记 section ===')
        const noteEditor = page.locator('textarea[aria-label="修炼日记编辑器"]')
        const hasNoteEditor = await noteEditor.isVisible({ timeout: 5000 }).catch(() => false)

        const noteTitle = page.locator('text=修炼日记')
        const hasNoteTitle = await noteTitle.first().isVisible({ timeout: 3000 }).catch(() => false)

        const saveNoteBtn = page.locator('button:has-text("保存心得")')
        const hasSaveNoteBtn = await saveNoteBtn.isVisible({ timeout: 3000 }).catch(() => false)

        console.log(`  "修炼日记" title visible: ${hasNoteTitle}`)
        console.log(`  Note editor (aria-label="修炼日记编辑器") visible: ${hasNoteEditor}`)
        console.log(`  "保存心得" button visible: ${hasSaveNoteBtn}`)

        const step8Pass = hasNoteEditor && hasNoteTitle
        results.step8 = step8Pass ? 'PASS' : 'FAIL'
        console.log(`  ${step8Pass ? '✅' : '❌'} Step 8 ${results.step8}: 修炼日记 section`)
        await page.screenshot({ path: 'e2e-results/step8-note-section.png' })

        // Step 9: Click 结束修习 and verify confirmation dialog
        console.log('\n=== Step 9: Click 结束修习 ===')
        let step9Pass = false

        if (hasEndButton) {
            await endButton.click()
            await page.waitForTimeout(2000)

            const confirmDialog = page.locator('[role="dialog"], [class*="ConfirmDialog"], [class*="confirm"], [class*="overlay"]')
            const hasConfirmDialog = await confirmDialog.first().isVisible({ timeout: 5000 }).catch(() => false)

            const bodyText = await page.textContent('body').catch(() => '')
            const hasEndConfirmContent = bodyText?.includes('结束修习') && (bodyText?.includes('继续修习') || bodyText?.includes('保存并结束'))

            console.log(`  Confirmation dialog visible: ${hasConfirmDialog}`)
            console.log(`  Dialog content includes expected text: ${hasEndConfirmContent}`)

            step9Pass = hasConfirmDialog || hasEndConfirmContent
            results.step9 = step9Pass ? 'PASS' : 'FAIL'
            console.log(`  ${step9Pass ? '✅' : '❌'} Step 9 ${results.step9}: Confirmation dialog`)

            await page.screenshot({ path: 'e2e-results/step9-confirm-dialog.png' })

            // Close dialog by clicking 继续修习
            const continueBtn = page.locator('button:has-text("继续修习")')
            if (await continueBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
                await continueBtn.click()
                await page.waitForTimeout(1000)
                console.log('  Clicked "继续修习" to close dialog')
            }
        } else {
            results.step9 = 'FAIL'
            console.log('  ❌ Step 9 FAIL: 结束修习 button not found')
        }

        // Step 10: Click 返回地图 and verify navigation back to hall
        console.log('\n=== Step 10: Click 返回地图 ===')
        let step10Pass = false

        await page.waitForTimeout(2000)

        let backBtn = page.locator('button[aria-label="返回地图"], button:has-text("返回地图")')
        let backBtnVisible = await backBtn.isVisible({ timeout: 5000 }).catch(() => false)

        if (!backBtnVisible) {
            const anyBackBtn = page.locator('a:has-text("返回地图"), [class*="backBtn"]')
            backBtnVisible = await anyBackBtn.isVisible({ timeout: 3000 }).catch(() => false)
            if (backBtnVisible) {
                backBtn = anyBackBtn
            }
        }

        if (backBtnVisible) {
            await backBtn.click()
            await page.waitForTimeout(3000)

            const finalUrl = page.url()
            const isBackToHall = finalUrl === `${BASE_URL}/` || finalUrl === BASE_URL
            console.log(`  Final URL: ${finalUrl}`)
            console.log(`  Navigated back to hall page: ${isBackToHall}`)

            const hallContent = await page.textContent('body').catch(() => '')
            const hasHallContent = hallContent?.includes('导师大厅') || hallContent?.includes('老夫子') || hallContent?.includes('秘境')
            console.log(`  Hall page content visible: ${hasHallContent}`)

            step10Pass = isBackToHall || hasHallContent
            results.step10 = step10Pass ? 'PASS' : 'FAIL'
            console.log(`  ${step10Pass ? '✅' : '❌'} Step 10 ${results.step10}: Navigation back to hall`)

            await page.screenshot({ path: 'e2e-results/step10-back-to-hall.png' })
        } else {
            results.step10 = 'FAIL'
            console.log('  ❌ Step 10 FAIL: 返回地图 button not found')
        }

        // Summary
        console.log('\n╔══════════════════════════════════════════════════╗')
        console.log('║            E2E TEST RESULTS SUMMARY             ║')
        console.log('╠══════════════════════════════════════════════════╣')
        console.log(`║ Step  1: Navigate to Hall page       - ${results.step1.padEnd(4)}       ║`)
        console.log(`║ Step  2: Hall page loads with NPCs    - ${results.step2.padEnd(4)}       ║`)
        console.log(`║ Step  3: Click NPC card (modal)       - ${results.step3.padEnd(4)}       ║`)
        console.log(`║ Step3.5: Click 开始修习               - ${startedDialogue ? 'PASS' : 'FAIL'}       ║`)
        console.log(`║ Step  4: Dialogue page elements       - ${results.step4.padEnd(4)}       ║`)
        console.log(`║ Step  5: Type message and send        - ${results.step5.padEnd(4)}       ║`)
        console.log(`║ Step  6: User message in chat         - ${results.step6.padEnd(4)}       ║`)
        console.log(`║ Step  7: NPC response in chat         - ${results.step7.padEnd(4)}       ║`)
        console.log(`║ Step  8: 修炼日记 section             - ${results.step8.padEnd(4)}       ║`)
        console.log(`║ Step  9: 结束修习 confirmation        - ${results.step9.padEnd(4)}       ║`)
        console.log(`║ Step 10: 返回地图 navigation          - ${results.step10.padEnd(4)}       ║`)
        console.log('╚══════════════════════════════════════════════════╝')
    })
})
