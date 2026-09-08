import type { FeedItem } from "@feedify/core";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "@/lib/theme";
import { router } from "expo-router";

type Props={item:FeedItem;onRepost?:(item:FeedItem)=>void;onUseful?:(item:FeedItem)=>void};
export function FeedCard({item,onRepost,onUseful}:Props){const t=useTheme();return <View style={[s.card,{backgroundColor:t.card,borderColor:t.line}]}>
  <Pressable onPress={()=>router.push(`/feed/${item.feedSlug}` as never)} style={s.metaRow}><View style={[s.feedMark,{backgroundColor:t.accent}]}><Text style={s.feedMarkText}>{item.feedEmoji}</Text></View><View style={{flex:1}}><Text style={[s.feedName,{color:t.text}]}>{item.feedName}</Text><Text style={[s.time,{color:t.muted}]}>{relative(item.createdAt)} · {item.kind}</Text></View></Pressable>
  {item.title?<Text style={[s.title,{color:t.text}]}>{item.title}</Text>:null}<Text style={[s.body,{color:t.text}]}>{item.body}</Text>
  <View style={[s.prov,{backgroundColor:t.dark?"#22241F":"#F0EFE8"}]}><Text style={[s.provText,{color:t.muted}]}>◇ {item.provenance.length} source{item.provenance.length===1?"":"s"} · tap feed for provenance</Text></View>
  <View style={s.actions}><Pressable onPress={()=>onUseful?.(item)} hitSlop={12}><Text style={[s.action,{color:t.muted}]}>♡ {item.likeCount||""}</Text></Pressable><Pressable onPress={()=>onRepost?.(item)} hitSlop={12}><Text style={[s.action,{color:t.muted}]}>↻ {item.repostCount||""}</Text></Pressable><Text style={[s.action,{color:t.muted}]}>◌ {item.commentCount||""}</Text><Text style={[s.action,{color:t.muted}]}>···</Text></View>
</View>}
function relative(iso:string){const h=Math.floor((Date.now()-new Date(iso).getTime())/3600000);return h<1?"now":h<24?`${h}h`: `${Math.floor(h/24)}d`;}
const s=StyleSheet.create({card:{borderWidth:1,borderRadius:24,padding:20,marginBottom:14},metaRow:{flexDirection:"row",alignItems:"center",gap:10},feedMark:{width:36,height:36,borderRadius:12,alignItems:"center",justifyContent:"center"},feedMarkText:{fontSize:18,fontWeight:"800",color:"#171813"},feedName:{fontSize:14,fontWeight:"700"},time:{fontSize:12,marginTop:2},title:{fontSize:22,lineHeight:27,fontWeight:"700",letterSpacing:-.4,marginTop:18,marginBottom:8},body:{fontSize:17,lineHeight:25,letterSpacing:-.15},prov:{alignSelf:"flex-start",borderRadius:10,paddingHorizontal:10,paddingVertical:7,marginTop:16},provText:{fontSize:12,fontWeight:"600"},actions:{flexDirection:"row",justifyContent:"space-between",paddingTop:18},action:{fontSize:14,fontWeight:"600"}});
