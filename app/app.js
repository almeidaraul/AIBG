const express = require('express')
const {spawn} = require('child_process')
const multer = require('multer')
const cors = require('cors')
const moment = require('moment')

const app = express()
const port = 3001
const storage = multer.memoryStorage()
const upload = multer({ storage: storage }).any();

app.use(cors());

app.get('/', (req, res) => {
	res.send('Hello World!')
})

app.post('/diaguard', upload, (req, res) => {
	fileContent = req.files[0].buffer.toString('utf8');
	const python = spawn('python3', ['analysis/get_json.py'], { stdio: ['pipe', 'pipe', 'pipe']});

	let input = '';
	let output = '';

	python.stdout.on('data', data => { output += data.toString() });
	python.stdin.write(fileContent);
	python.stdin.end();

	python.on('close', (code) => {
		let json_output = JSON.parse(output.replace(/\bNaN\b/g, "null"));
		// for unix epoch:
		// json_output.table.Date = json_output.table.Date.map(dateStr => moment(dateStr, "YYYY-MM-DD h:mm:ss").unix());
		console.log(`python close code: ${code}`)
		res.header('Acess-Control-Allow-Origin', 'true');
		res.status(200).send({...json_output
		})
	});
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})
