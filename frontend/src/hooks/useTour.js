import Shepherd from 'shepherd.js'
import 'shepherd.js/dist/css/shepherd.css'

const STEPS = [
  {
    id: 'welcome',
    text: `<strong>Welcome to JobSearch AI!</strong><br><br>
      This quick tour will walk you through the app.
      You can exit at any time by pressing <strong>Esc</strong> or clicking outside.`,
    attachTo: { element: '.app-brand', on: 'bottom' },
  },
  {
    id: 'tabs',
    text: `<strong>Navigation tabs</strong><br><br>
      <strong>Generate</strong> — create a new cover letter or "Why This Company" answer.<br>
      <strong>History</strong> — browse and revisit everything you've generated.`,
    attachTo: { element: '.tabs', on: 'bottom' },
  },
  {
    id: 'generate-panel',
    text: `<strong>Generate tab</strong><br><br>
      A 3-step wizard guides you through the process. The step indicator at the top
      shows where you are — you can click a completed step to go back.`,
    attachTo: { element: '.wizard-steps', on: 'bottom' },
  },
  {
    id: 'resume-step',
    text: `<strong>Step 1 — Resume</strong><br><br>
      Upload a new PDF resume or pick one you've saved before.
      Uploaded resumes are stored to your account so you can reuse them.`,
    attachTo: { element: '.resume-mode-toggle', on: 'bottom' },
  },
  {
    id: 'output-options',
    text: `<strong>Step 2 — Choose your outputs</strong><br><br>
      <strong>Cover Letter</strong> — a tailored, structured letter for the role.<br>
      <strong>Why This Company</strong> — a 2–4 sentence answer to "Why do you want to work here?", specific to the company.<br><br>
      Check one or both. The Generate button won't activate until at least one is selected.`,
    attachTo: { element: '.output-options', on: 'top' },
    beforeShowPromise: () =>
      new Promise((resolve) => {
        const el = document.querySelector('.output-options')
        if (el) return resolve()
        // If not visible yet (user is on step 1), skip gracefully
        resolve()
      }),
  },
  {
    id: 'history',
    text: `<strong>History tab</strong><br><br>
      Every generation is saved here. Click any entry to expand it and see the
      full cover letter, Why This Company answer, and fit analysis. You can also
      delete entries you no longer need.`,
    attachTo: { element: '.tabs button:nth-child(2)', on: 'bottom' },
  },
  {
    id: 'help-button',
    text: `<strong>That's it!</strong><br><br>
      Click the <strong>?</strong> button any time to replay this tour.`,
    attachTo: { element: '.btn-help', on: 'left' },
  },
]

export function useTour(isAdmin) {
  const startTour = () => {
    const tour = new Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        cancelIcon: { enabled: true },
        scrollTo: { behavior: 'smooth', block: 'center' },
        buttons: [
          {
            text: 'Back',
            classes: 'shepherd-btn-back',
            action() { this.back() },
          },
          {
            text: 'Next',
            classes: 'shepherd-btn-next',
            action() { this.next() },
          },
        ],
      },
    })

    const steps = isAdmin ? STEPS : STEPS.filter((s) => s.id !== 'admin-note')

    steps.forEach((step, i) => {
      const isFirst = i === 0
      const isLast = i === steps.length - 1

      tour.addStep({
        ...step,
        buttons: [
          ...(isFirst ? [] : [{ text: 'Back', classes: 'shepherd-btn-back', action() { this.back() } }]),
          {
            text: isLast ? 'Done' : 'Next',
            classes: 'shepherd-btn-next',
            action() { isLast ? this.complete() : this.next() },
          },
        ],
        when: {
          show() {
            // Skip steps whose target element doesn't exist
            const target = step.attachTo?.element
            if (target && !document.querySelector(target)) {
              tour.next()
            }
          },
        },
      })
    })

    tour.start()
  }

  return { startTour }
}
