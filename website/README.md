# Your portfolio website — the simple guide

## What's in this folder

| File | What it is |
|---|---|
| `index.html` | **The words on your website.** This is the one you'll edit most. |
| `styles.css` | How it looks: colours, fonts, spacing. |
| `script.js` | Small extras: dark mode button, phone menu, fade-in effects. No need to touch it. |
| `favicon.svg` | The little icon in the browser tab. |
| `404.html` | The page people see if they type a wrong address. |
| `images/` | Put your photos here. |
| `fonts/` | The Persian font (Vazirmatn), stored inside the site so it loads even where Google is blocked. Don't touch. |
| `vendor/three.min.js` | The free 3D engine (Three.js) that draws the moving 3D shape. Don't touch. |

The whole site is in **Persian, right-to-left**. Persian text goes in exactly like any text: just type or paste it between the tags.

## How to change the text

1. Open `index.html` (on GitHub: click the file, then the ✏️ pencil icon).
2. Look for lines marked **`✏️ EDIT`**. The text right below each one is what you change.
3. Only change the words **between** the `<tags>`. For example, in
   `<h3>Lumen Finance</h3>` you change only `Lumen Finance`.
4. Click **Commit changes**. About a minute later the live site updates by itself.

## How to add a picture

1. In the `images` folder on GitHub, click **Add file → Upload files** and upload your picture (for example `me.jpg`).
2. In `index.html`, follow the `✏️ EDIT` note in the "About" or "Projects" section. It tells you which line to swap.

Tip: shrink big photos first (https://squoosh.app is free) so the site stays fast.

## How to change the colours

Open `styles.css`. The first block, marked `✏️ COLOURS`, lists every colour. Change a code like `#c2502e` to any colour you like (pick one at https://htmlcolorcodes.com).

## The 3D parts

- **The 3D shape at the top** follows the mouse and gently floats. To change its colour, open `script.js`, find the block marked `✏️ 3D SETTINGS`, and change the codes after `0x` (for example `0xc2502e` → `0x2e6bc2` for blue).
- **The cards tilt in 3D** when the mouse moves over them. This works automatically for any card you add, as long as it keeps `tilt` in its `class="..."`.
- On phones the shape sits softly behind the text. For visitors whose device asks for "less motion", it stays still.
- If a very old device can't show 3D, a simple coloured ball appears instead. Nothing breaks.

## Putting it online for free (Cloudflare Pages)

1. Create a free account at https://dash.cloudflare.com
2. Go to **Workers & Pages → Create → Pages → Connect to Git**.
3. Connect your GitHub account and choose the repository **sampleapp**.
4. Fill in the settings exactly like this:
   - **Production branch:** the branch that holds this website (`main` once it's merged there)
   - **Framework preset:** `None`
   - **Build command:** *(leave empty)*
   - **Build output directory:** `website`
5. Click **Save and Deploy**. You'll get a free address like `your-name.pages.dev`.

From then on, every change you save on GitHub goes live automatically.

**Want your own address (like `yourname.com`)?** That's the one part that costs money, about €10 a year. You can buy one inside Cloudflare (**Domain Registration**) and connect it under your Pages project → **Custom domains**.
