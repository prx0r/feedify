import { useMutation,useQuery,useQueryClient } from "@tanstack/react-query";
import { router,useLocalSearchParams } from "expo-router";
import { Pressable,SafeAreaView,ScrollView,StyleSheet,Text,View } from "react-native";
import type { OutputType } from "@feedify/core";
import * as api from "@/lib/api";import { useTheme } from "@/lib/theme";

const addable:Array<{type:OutputType;name:string;blurb:string;config?:Record<string,unknown>}>= [
  {type:"x_bot",name:"X bot",blurb:"Autopost or smart-repost the strongest items.",config:{strategy:"smart",dryRun:true,minScore:.72}},
  {type:"x402",name:"x402 API",blurb:"Sell machine access to this feed over HTTP 402.",config:{price:"$0.01",network:"eip155:8453",path:"latest"}},
  {type:"webhook",name:"Webhook",blurb:"Push every new item into another product.",config:{dryRun:true}},
  {type:"blog",name:"Blog",blurb:"Compile the stream into persistent articles.",config:{format:"markdown"}},
  {type:"report",name:"Reports",blurb:"Turn windows of signal into research reports.",config:{cadence:"weekly"}},
];
export default function Products(){
 const{id}=useLocalSearchParams<{id:string}>();const t=useTheme(),qc=useQueryClient();
 const fq=useQuery({queryKey:["feed",id],queryFn:()=>api.feed(id!)});const pq=useQuery({queryKey:["products",id],queryFn:()=>api.products(id!)});
 const add=useMutation({mutationFn:(x:(typeof addable)[number])=>api.addProduct(id!,{type:x.type,name:x.name,config:x.config}),onSuccess:()=>qc.invalidateQueries({queryKey:["products",id]})});
 const feed=fq.data?.feed,outputs=pq.data||[];if(!feed)return <SafeAreaView style={{flex:1,backgroundColor:t.bg}}/>;
 const existing=new Set(outputs.map(x=>x.type));
 return <SafeAreaView style={[s.safe,{backgroundColor:t.bg}]}><ScrollView contentContainerStyle={s.content}>
  <Pressable onPress={()=>router.back()}><Text style={[s.back,{color:t.text}]}>‹ Back</Text></Pressable>
  <Text style={[s.kicker,{color:t.muted}]}>FEED → PRODUCTS</Text><Text style={[s.hero,{color:t.text}]}>{feed.name}</Text>
  <Text style={[s.desc,{color:t.muted}]}>Compile the signal once. Every product below reads the same immutable items and provenance.</Text>
  <View style={s.chain}>{outputs.filter(x=>x.enabled).map((o,i)=><View key={o.id} style={s.chainRow}><View style={[s.dot,{backgroundColor:t.accent}]}/><Text style={[s.chainText,{color:t.text}]}>{i===0?"Feed":"↳"} {o.name}</Text></View>)}</View>
  <Text style={[s.section,{color:t.text}]}>Add an output</Text>
  {addable.map(x=><View key={x.type} style={[s.card,{borderColor:t.line,backgroundColor:t.card}]}><View style={{flex:1}}><Text style={[s.cardTitle,{color:t.text}]}>{x.name}</Text><Text style={[s.cardText,{color:t.muted}]}>{x.blurb}</Text></View><Pressable disabled={existing.has(x.type)||add.isPending} onPress={()=>add.mutate(x)} style={[s.add,{backgroundColor:existing.has(x.type)?t.line:t.accent}]}><Text style={s.addText}>{existing.has(x.type)?"Added":"Add"}</Text></Pressable></View>)}
  <Text style={[s.note,{color:t.muted}]}>X outputs start in dry-run mode. x402 becomes live when the gateway has a pay-to address and the creator enables deployment credentials.</Text>
 </ScrollView></SafeAreaView>
}
const s=StyleSheet.create({safe:{flex:1},content:{padding:18,paddingTop:12,paddingBottom:100},back:{fontSize:16,fontWeight:"700",marginBottom:24},kicker:{fontSize:11,fontWeight:"900",letterSpacing:1.4},hero:{fontSize:35,fontWeight:"800",letterSpacing:-1.3,marginTop:8},desc:{fontSize:16,lineHeight:23,marginTop:12},chain:{marginTop:24,gap:10},chainRow:{flexDirection:"row",alignItems:"center",gap:10},dot:{width:9,height:9,borderRadius:9},chainText:{fontSize:15,fontWeight:"700"},section:{fontSize:20,fontWeight:"800",marginTop:34,marginBottom:10},card:{borderWidth:1,borderRadius:20,padding:16,marginTop:10,flexDirection:"row",alignItems:"center",gap:12},cardTitle:{fontSize:16,fontWeight:"800"},cardText:{fontSize:12,lineHeight:17,marginTop:4,maxWidth:240},add:{borderRadius:99,paddingHorizontal:14,paddingVertical:9},addText:{fontSize:12,fontWeight:"900",color:"#151612"},note:{fontSize:11,lineHeight:17,marginTop:22}});
