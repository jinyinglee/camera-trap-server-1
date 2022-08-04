const path = require('path');
const Dotenv = require('dotenv-webpack');

module.exports = (env) => {
  const env_name = (env.myenv === 'dev') ? '.dev.js' : '.min.js';
  const env_path = (env.myenv === 'dev') ? path.join(__dirname, '../static/js') : path.join(__dirname, 'dist');
  return {
    entry: {
      'search': './src/search.js',
    },
    output: {
      path: env_path,
      filename: `[name]${env_name}`,
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          loader: 'babel-loader'
        },
      ],
    },
    devtool: 'source-map',
    plugins: [
      new Dotenv({
        path: (env.myenv === 'prod') ? '.env.prod' : '.env',
      }),
    ]
  }
};
