[200~
from flask import Flask
from flask_cors import CORS
from werkzeug.datastructures import FileStorage
from flask_restx import Api, Resource, Namespace, reqparse
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

import spacy
from pdfminer.high_level import extract_text

nlp = spacy.load(model_path)

def parse_resume(file_path):
    text = extract_text(file_path)
    doc = nlp(text)

    resp = dict()

    for ent in doc.ents:
        if resp.get(ent.label_) is None:
            resp[ent.label_] = [ent.text]
        else:
            resp[ent.label_].append(ent.text)

    return resp

def count_matcher(job_description, resumes):
    vectorizer = CountVectorizer().fit_transform([job_description, resumes])
    vectors = vectorizer.toarray()

    job_vector = vectors[0]
    resume_vectors = vectors[1:]
    similarities = cosine_similarity([job_vector], resume_vectors)[0]
    print(similarities)

    return similarities

def tfidf_matcher(job_description, resumes):
    vectorizer = TfidfVectorizer().fit_transform([job_description, resumes])
    vectors = vectorizer.toarray()

    job_vector = vectors[0]
    resume_vectors = vectors[1:]
    similarities = cosine_similarity([job_vector], resume_vectors)[0]
    print(similarities)

    return similarities

api = Api(
    app=app,
    version='1.0',
    title='Resume Parser',
    description='Resume Parser API',
    doc='/',
    validate=True
)

resume_parser_args = reqparse.RequestParser()
resume_parser_args.add_argument('resume', type=FileStorage, location='files')
resume_parser_args.add_argument('job_description', type=str, location='form')

resume_args = reqparse.RequestParser()
resume_args.add_argument('resume', type=FileStorage, location='files')

resume_parser_controller = Namespace(
    name = 'Resume Parser Controller',
    description='Send the job description and resume to get similarity score.',
    path='/resume-parser'
)

@resume_parser_controller.route('/get-similarity')
class ResumeParserController(Resource):
    @resume_parser_controller.expect(resume_parser_args)
    def post(self):
        args = resume_parser_args.parse_args()
        resume = args['resume']
        job_description = args['job_description']
        resume.save('resume.pdf')
        resume_text = extract_text('resume.pdf')

        score = tfidf_matcher(job_description, resume_text)                 if tfidf_matcher(job_description, resume_text) > count_matcher(job_description, resume_text)                 else count_matcher(job_description, resume_text)


        return {
            'score' : score[0]
        }

@resume_parser_controller.route('/parse')
class ResumeController(Resource):
    @resume_parser_controller.expect(resume_args)
    def post(self):
        args = resume_args.parse_args()
        resume = args['resume']
        resume.save('/content/drive/MyDrive/resume-parser/test/resume.pdf')

        return parse_resume('/content/drive/MyDrive/resume-parser/test/resume.pdf')

api.add_namespace(resume_parser_controller)

if __name__ == '__main__':
    app.run()

