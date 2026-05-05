# React + Vite Project

This project is built with [React](https://reactjs.org/) and [Vite](https://vitejs.dev/).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm run build`

Builds the app for production to the `dist` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

### `npm run serve`

Previews the production build locally.

## Learn More

To learn more about the technologies used in this project:

- [React Documentation](https://reactjs.org/)
- [Vite Documentation](https://vitejs.dev/guide/)
- [React Router Documentation](https://reactrouter.com/)
- [Styled Components Documentation](https://styled-components.com/docs)


## Deployment

### Staging Environment
This repository automatically deploys to staging at https://docs.ciroh.org/ngiab-website-staging when changes are pushed to the main branch.

### Production Deployment

To sync to production:

#### Option 1: Direct Push (Immediate)
```bash
# Add production remote (one-time setup)
git remote add production https://github.com/CIROH-UA/ngiab-website.git

# Push directly to production
git push production main
```
LL
#### Option 2: Tagged Release (Automated)
```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions will automatically sync to production
```

**Note**: Both methods work! Use direct push for immediate deployment, or tagged releases for versioned deployments.
