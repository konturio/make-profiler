# Makefile Profiler Report

Reports large data processing pipeline steps.  

## Usage
Creates report.json file under report folder.  
Includes status & pipeline information.  
Logs, event time & description of each Makefile process is stated on status.  
Present status of pipeline, number of progress and failed jobs are stated on pipeline.  
index.html consumes and reports last status.  
  
Any process can be searched on UI.  
Failed & idle tasks are reported with red & yellow colors.  
All fields can be sorted.  
  
run "npm install" to add dependencies  
run if there is babel error "sudo npm cache clean --force"  
add report.jsn under public folder for test  

run to start app:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.