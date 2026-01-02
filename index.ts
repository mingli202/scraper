import { GoogleGenAI, type File } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GOOGLE_API_KEY });

async function uploadPdf(pdfPath: string): Promise<File> {
  const file = await ai.files.upload({
    file: "/Users/vincentliu/Downloads/SCHEDULE_OF_CLASSES_Winter_2026_December_11.pdf",
    config: {
      mimeType: "application/pdf",
    },
  });

  return file;
}

async function main() {
  const response = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
    contents: "I want to go to the beach in Hawaii",
  });
  console.log(response);
}

