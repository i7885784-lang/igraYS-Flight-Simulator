#include <ysclass.h>
#include <ysport.h>

#include <ysshelldnmident.h>
#include <ysshellext_orientationutil.h>

#include "fsvisual.h"


FsVisualSrf::FsVisualSrf(const FsVisualSrf &incoming)
{
	YsShellExt::CopyFrom(incoming);
}
FsVisualSrf &FsVisualSrf::operator=(const FsVisualSrf &incoming)
{
	vboSet.CleanUp();
	YsShellExt::CopyFrom(incoming);
	return *this;
}

YSRESULT FsVisualSrf::Load(const wchar_t fn[])
{
	YsFileIO::File fp(fn,"r");
	if(nullptr!=fp.Fp())
	{
		auto inStream=fp.InStream();
		return YsVisualSrf::Load(inStream);
	}
	return YSERR;
}


////////////////////////////////////////////////////////////


FsVisualDnm::FsVisualDnm()
{
	specialRenderingRequirment=RENDER_NORMAL;
	papiAngle=0.0;
}
FsVisualDnm::FsVisualDnm(std::nullptr_t)
{
	specialRenderingRequirment=RENDER_NORMAL;
	papiAngle=0.0;
}
FsVisualDnm::~FsVisualDnm()
{
}
YSRESULT FsVisualDnm::Load(const wchar_t fn[])
{
    afterburnerGeometryCache=-1;
	YsString fnUtf8;
	fnUtf8.EncodeUTF8(fn);

	YsFileIO::File fp(fn,"r");
	if(nullptr!=fp.Fp())
	{
		auto inStream=fp.InStream();
		return YsVisualDnm::Load(inStream,fnUtf8);
	}
	return YSERR;
}

bool FsVisualDnm::HasAfterburnerGeometry(void) const
{
    if(nullptr==dnmPtr) return false;
    if(afterburnerGeometryCache<0)
    {
        afterburnerGeometryCache=0;
        for(auto node : dnmPtr->GetNodePointerAll()) if(2==node->dnmClassType || 112==node->dnmClassType || 113==node->dnmClassType) { afterburnerGeometryCache=1;break; }
    }
    return 0<afterburnerGeometryCache;
}
