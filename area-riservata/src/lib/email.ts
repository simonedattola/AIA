import nodemailer from "nodemailer";
import { formatDateTime } from "./utils";

export async function sendReminderEmail(
  to: string,
  eventTitle: string,
  eventDate: Date
): Promise<boolean> {
  const host = process.env.SMTP_HOST;
  if (!host) {
    console.log(`[reminder mock] ${to}: ${eventTitle} @ ${formatDateTime(eventDate)}`);
    return false;
  }

  const transporter = nodemailer.createTransport({
    host,
    port: Number(process.env.SMTP_PORT || 587),
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });

  await transporter.sendMail({
    from: process.env.SMTP_FROM || "noreply@aia-legnano.it",
    to,
    subject: `Reminder: ${eventTitle}`,
    text: `Promemoria evento: ${eventTitle}\nData: ${formatDateTime(eventDate)}`,
  });
  return true;
}
