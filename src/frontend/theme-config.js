/**
 * Theme Configuration
 *
 * Defines available visual style themes for the application.
 * Each theme includes both light and dark mode variants.
 */

export const THEMES = {
  'kraft-paper': {
    id: 'kraft-paper',
    name: 'Kraft Paper',
    description: 'Warm kraft paper aesthetic with natural tones',
    file: 'styles/themes/kraft-paper.css',
    fonts: {
      sans: 'Chocolate Classical Sans',
      serif: 'Alice',
      mono: 'Courier Prime'
    }
  },
  'notebook': {
    id: 'notebook',
    name: 'Notebook',
    description: 'Grayscale notebook style with handwritten font',
    file: 'styles/themes/notebook.css',
    fonts: {
      sans: 'Architects Daughter',
      serif: 'Times New Roman',
      mono: 'Courier New'
    }
  },
  'blue-on-black': {
    id: 'blue-on-black',
    name: 'Blue on Black',
    description: 'Modern blue and purple accents',
    file: 'styles/themes/blue_on_black.css',
    fonts: {
      sans: 'Afacad',
      serif: 'Alice',
      mono: 'Courier Prime'
    }
  },
  'gold-on-blue': {
    id: 'gold-on-blue',
    name: 'Gold on Blue',
    description: 'Elegant gold on blue with serif typography',
    file: 'styles/themes/gold_on_blue.css',
    fonts: {
      sans: 'Libre Baskerville',
      serif: 'Georgia',
      mono: 'Consolas'
    }
  },
  'graphite': {
    id: 'graphite',
    name: 'Graphite',
    description: 'Professional grayscale with modern sans-serif',
    file: 'styles/themes/graphite.css',
    fonts: {
      sans: 'Montserrat',
      serif: 'Georgia',
      mono: 'Fira Code'
    }
  }
};

export const DEFAULT_THEME = 'kraft-paper';

export function getThemeList() {
  return Object.values(THEMES);
}

export function getTheme(id) {
  return THEMES[id] || THEMES[DEFAULT_THEME];
}
