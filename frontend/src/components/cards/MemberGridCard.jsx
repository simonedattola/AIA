import { memo } from "react";
import { Link } from "react-router-dom";
import { Card, CardTitle, Eyebrow } from "@/design-system";
import MediaImage from "../MediaImage";
import { memberRoleLabel } from "../../lib/memberRoles";

function MemberGridCard({ member }) {
  const to = member.slug ? `/arbitri/${member.slug}` : "#";
  return (
    <Card as={Link} to={to} interactive padding="none" className="overflow-hidden hover:border-navy-600 block">
      <div className="aspect-square bg-slate-100 overflow-hidden">
        {member.photoUrl ? (
          <MediaImage src={member.photoUrl} alt="" className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-navy-600 text-white font-display text-2xl font-bold">
            {member.firstName[0]}
            {member.lastName[0]}
          </div>
        )}
      </div>
      <div className="p-4">
        <Eyebrow as="div" className="text-gold-600 tracking-wider mb-1">
          {memberRoleLabel(member)}
        </Eyebrow>
        <CardTitle as="h3">
          {member.firstName} {member.lastName}
        </CardTitle>
        {member.category && <p className="text-sm text-slate-500 mt-1">{member.category}</p>}
      </div>
    </Card>
  );
}

export default memo(MemberGridCard);
