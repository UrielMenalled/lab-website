# The Agroecology Lab - GitHub Pages Website

A multi-page website for The Agroecology Lab at Montana State University, designed for deployment on GitHub Pages.

## Structure

```
public/
├── index.html          # Homepage
├── team.html           # Meet the Team
├── research.html       # Research Areas
├── teaching.html       # Teaching Experience
├── publications.html   # Publications List
├── join.html           # Join Us / Prospective Students
└── styles.css          # Shared stylesheet
```

## Deployment to GitHub Pages

### Option 1: Using the `public` folder directly

1. Create a new GitHub repository
2. Push your code to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
3. Go to your repository Settings → Pages
4. Under "Source", select "Deploy from a branch"
5. Select the `main` branch and `/public` folder
6. Click Save
7. Your site will be available at `https://<username>.github.io/<repository-name>/`

### Option 2: Using GitHub Actions

1. Create a new GitHub repository
2. Push your code to the repository
3. Go to Settings → Pages
4. Under "Source", select "GitHub Actions"
5. Create a workflow file at `.github/workflows/deploy.yml`:
   ```yaml
   name: Deploy to GitHub Pages

   on:
     push:
       branches: ["main"]

   permissions:
     contents: read
     pages: write
     id-token: write

   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/configure-pages@v3
         - uses: actions/upload-pages-artifact@v2
           with:
             path: 'public'
         - uses: actions/deploy-pages@v2
   ```

## Local Development

To view the site locally:

1. Navigate to the `public` folder:
   ```bash
   cd public
   ```

2. Start a local server:
   ```bash
   # Using Python 3
   python -m http.server 8000

   # Using Python 2
   python -m SimpleHTTPServer 8000

   # Using Node.js
   npx serve
   ```

3. Open your browser to `http://localhost:8000`

## Features

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Consistent Navigation**: All pages share the same header and footer
- **SEO Optimized**: Meta tags on each page for search engines
- **Professional Styling**: Clean, academic design with Montana State University branding
- **Accessible**: Semantic HTML and proper heading hierarchy

## Customization

### Updating Colors

Edit the CSS variables in `public/styles.css`:

```css
:root {
  --primary-green: #2c5f2d;    /* Main brand color */
  --accent-orange: #d97a34;     /* Accent color */
  --text-dark: #2d2d2d;         /* Body text */
  --text-light: #666;           /* Secondary text */
  --background-light: #f8f8f8;  /* Background sections */
}
```

### Adding New Pages

1. Create a new HTML file in the `public` folder
2. Copy the header and footer from an existing page
3. Add a link to the new page in the navigation menu of all pages

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This website template is for academic use. Content belongs to The Agroecology Lab at Montana State University.
