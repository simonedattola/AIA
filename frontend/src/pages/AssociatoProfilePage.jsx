import { useParams } from "react-router-dom";
import MemberProfileContent from "../components/members/MemberProfileContent";

export default function AssociatoProfilePage() {
  const { slug } = useParams();
  return <MemberProfileContent memberSlug={slug} />;
}
