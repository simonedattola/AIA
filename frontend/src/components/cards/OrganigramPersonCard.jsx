import { memo } from "react";
import { Link } from "react-router-dom";
import { Card, CardTitle, Eyebrow } from "@/design-system";
import MediaImage from "../MediaImage";

function OrganigramPersonCard({ member, subtitle }) {
  const to = member.slug ? `/arbitri/${member.slug}` : "#";
  return (
    <Card as={Link} to={to} interactive padding="none" className="overflow-hidden block">
      <div className="aspect-square overflow-hidden bg-slate-100">
        {member.photoUrl ? (
          <MediaImage src={member.photoUrl} alt="" className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-navy-600 text-white font-display text-3xl font-bold">
            {member.firstName[0]}
            {member.lastName[0]}
          </div>
        )}
      </div>
      <div className="p-4">
        <Eyebrow as="div" className="text-gold-600 tracking-wider mb-1">
          {subtitle}
        </Eyebrow>
        <CardTitle as="h3">
          {member.firstName} {member.lastName}
        </CardTitle>
      </div>
    </Card>
  );
}

export default memo(OrganigramPersonCard);
