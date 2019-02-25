![Reference Bot](bot.png)

**\*Beep\*** _\*boop\*_ I’m `@referencebot`! A bot who can build [IATI Reference](http://reference.iatistandard.org) sites 🚀

Once you’ve completed the setup, you can write "@referencebot build!" in a pull request comment, and I’ll build a staging site for you.

## Setup

You need to add a webhook to your organization, so I can be notified whenever you mention my name.

 1. Visit [https://github.com/settings/organizations](https://github.com/settings/organizations) and select the relevant organization
 2. Click **"Settings"** to see the settings for your organization
 3. In the sidebar, click **"Webhooks"**. Then near the top-right, you’ll see an **"Add webhook"** button. Click it!
 4. You’ll see a form to add a new webhook. Webhooks are fired whenever some specified action happens on github.
 5. First, set the Payload URL to [https://referencebot.herokuapp.com/github](https://referencebot.herokuapp.com/github)
 6. Set the "Content type" to "**application/json**"
 7. Leave the "Secret" and "SSL verification" as default
 8. For "Which events would you like to trigger this webhook?", choose "**Let me select individual events.**" Then ensure only the following two checkboxes are checked:
     * **"Issue comments"**, and
     * **"Pull requests"**
 9. Leave "Active" checked, and click **"Add webhook"**

## Usage

Mention "@referencebot" and "build" in a pull request comment, and I’ll do the rest!
