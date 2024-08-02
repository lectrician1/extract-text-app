import { promises as fs } from "node:fs";
import { pdf } from "pdf-to-img";
import { v4 as uuidv4 } from "uuid";
import path from "path";
import { json } from "@sveltejs/kit";

export const POST = async ({ request }) => {
  const data = await request.formData();
  const pdfFile = data.get("pdf");

  if (!pdfFile || pdfFile.size === 0) {
    return json({ error: "No PDF file uploaded" }, { status: 400 });
  }

  const tempFilePath = path.join("/tmp", `${uuidv4()}.pdf`);
  const fileBuffer = Buffer.from(await pdfFile.arrayBuffer());

  await fs.writeFile(tempFilePath, fileBuffer);

  try {
    const document = await pdf(tempFilePath, { scale: 3 });
    const images = [];
    let counter = 1;
    for await (const image of document) {
      const base64Image = image.toString("base64");
      images.push(`data:image/png;base64,${base64Image}`);
      counter++;
    }
    await fs.unlink(tempFilePath);
    return json({ images });
  } catch (error) {
    await fs.unlink(tempFilePath);
    return json({ error: error.message }, { status: 500 });
  }
};
