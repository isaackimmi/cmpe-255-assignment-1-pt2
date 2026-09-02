import { Card } from "@mui/material";
import { FEATURES, FEATURE_KEYS } from "../../constants/features";
import { formatNumber } from "../../utils/format";
import { SelectField } from "../common/SelectField";
import { SectionHeading } from "../common/SectionHeading";

export function ProfileLens({ profiles, cluster, feature, onFeatureChange }) {
  const visible = profiles.filter((profile) => cluster === "all" || String(profile.cluster) === cluster);
  const max = Math.max(...profiles.map((profile) => profile.means[feature]), 1);
  const selector = <SelectField id="profile-feature" label="Compare feature" value={feature} onChange={(event) => onFeatureChange(event.target.value)} options={FEATURE_KEYS.map((key) => ({ value: key, label: FEATURES[key] }))} />;
  return (
    <Card component="article" className="panel">
      <SectionHeading eyebrow="PROFILE LENS" title="Who is in each segment?" action={selector} />
      <div className="profiles">{visible.map((profile) => <article className="profile" key={profile.cluster}><div className="profile-top"><span>SEGMENT {profile.cluster}</span><b>{profile.count} customers</b></div><h3>{profile.name}</h3><p>{profile.guidance}</p><div className="bar"><i style={{ width: `${Math.max(8, profile.means[feature] / max * 100)}%` }} /></div><strong>{FEATURES[feature]} · {formatNumber(profile.means[feature], 1)}</strong><div className="mini-grid">{FEATURE_KEYS.map((key) => <span key={key}>{FEATURES[key]}<b>{formatNumber(profile.means[key], key === "purchase_frequency" ? 1 : 0)}</b></span>)}</div></article>)}</div>
    </Card>
  );
}
